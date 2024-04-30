from opensearchpy import OpenSearch
from enum import Enum
import config
import pandas as pd
import logging
from modules.EmbeddingModel import EmbeddingModels
from modules.EmbeddingModel import BGME3_EMB

logger = logging.getLogger()
logger.setLevel(logging.INFO)
opensearch_logger = logging.getLogger("opensearch")
opensearch_logger.setLevel(logging.WARN)

from modules.HyperClovaX import HyperClovaX


class OpenSearchHelper():
    def __init__(self):
        OSH_CONFIG = config.OPENSEARCH
        EMB_CONFIG = config.HCX_EMBEDDING
        self.host = OSH_CONFIG['HOST']
        self.port = 9200
        self.auth = (OSH_CONFIG['ID'], OSH_CONFIG['PASSWD'])
        self.clova_studio_api_key=EMB_CONFIG['X-NCP-CLOVASTUDIO-API-KEY']
        self.apigw_api_key=EMB_CONFIG['X-NCP-APIGW-API-KEY']
        self.emb_appId = EMB_CONFIG['APP_ID']
        self.embedding_model_ncp=True

        self.client = self.getClient()


    def getClient(self) -> dict:
        client = OpenSearch(
            hosts=[{'host': self.host, 'port': self.port}],
            http_compress = True, # enables gzip compression for request bodies
            http_auth = self.auth,
            use_ssl = True,
            verify_certs = False,
            ssl_assert_hostname = False,
            ssl_show_warn = False,
            timeout = 300
        )
        
        return client
        
    def get_document_count(self, index) -> int:
        cnt = self.client.count(index=index)
        return cnt

    def get_indices(self, prefix) -> dict :
        indices = [i for i in self.client.indices.get_alias(f'{prefix}*')]
        if len(indices) == 0:
            return {}
        else:
            indices_dict = self.client.indices.get(index=indices)
            return indices_dict
    
    def create_index(self, session_sate) -> None:
        index_name = f'ncp_edu_{session_sate["index_name"]}'
        index_body = {
            "settings": {
                "index": {
                "knn": True,
                "knn.algo_param.ef_search": session_sate['ef_search']
                }
            },
            "mappings": {
                "properties": {
                    "origin-question":{
                        "type": "text"
                    },
                    "origin-text":{
                        "type": "text"
                    },
                    ("emb-model--" + session_sate['embedding_model_name']): {
                        "type": "text"
                    },
                    "vector": {
                    "type": "knn_vector",
                    "dimension": session_sate['dimension'],
                    "method": {
                        "name": "hnsw",
                        "space_type": session_sate['space_type'],
                        "engine": "nmslib",
                        "parameters": {
                        "ef_construction": session_sate['ef_construction'],
                        "m": session_sate['m']
                        }
                    }
                    }
                }
            }
        }
        self.client.indices.create(index=index_name, body=index_body)

    def delete_index(self, index) -> None :
        self.client.indices.delete(index=index)

    def load_sc2_data(self, index, session_state) -> None:
        df_csv = pd.read_csv(filepath_or_buffer='data/starcraft2.csv')
        
        origin_question = []
        origin_text = []
        embedding_text = []
        model_name = session_state['embedding_model_name']

        for idx, line in df_csv.iterrows():
            logger.info(f"\x1b[32m embedding {idx + 1} / {len(df_csv['Completion'])}")
            res_vector = self.text_to_vector(text=line['Completion'], model_name=model_name)
            if res_vector != []:
                embedding_text.append(res_vector)
                origin_question.append(line['Text'])
                origin_text.append(line['Completion'])
            else:
                None


        if len(origin_text) == len(embedding_text):
            dt_dict = {'origin-question': origin_question, 'origin_text': origin_text, 'embedding_text': embedding_text}
            df_final = pd.DataFrame(dt_dict)
            self.bulk_insert(data=df_final, index=index)


    def bulk_insert(self, data, index) -> None :
        datas = []
        for idx, line in data.iterrows():
            index_no = { "index" : { "_index" : (index), "_id" : (idx + 1)} }
            data =  {"origin-question": line['origin-question'], "origin-text": line['origin_text'], "vector": line['embedding_text']}
            datas.append(index_no)
            datas.append(data)
        self.client.bulk(datas)

    def text_to_vector(self, text, model_name) -> list:
        if model_name in [EmbeddingModels.HCX_STS_DOLPHIN.value, EmbeddingModels.HCX_EMB_DOLPHIN.value]:
            hcx = HyperClovaX(clova_studio_api_key = self.clova_studio_api_key, apigw_api_key = self.apigw_api_key)
            hcx.set_embedding(app_id=self.emb_appId, model_name=model_name)
            res = hcx.embedding(text=text)

            if res.status_code == 200 :
                return res.json()['result']['embedding']
            else:
                logger.error(f"\x1b[31m text_to_vector_ERROR")
                return []
        elif model_name in [EmbeddingModels.BGE_M3.value]:
            bgme3_model = BGME3_EMB(encoding=model_name)
            res = bgme3_model.do_embeding(text=text)
            return res
            

        

    def normal_search(self, text, model_name, index) -> dict:
        vector = self.text_to_vector(text=text, model_name=model_name)
        search_body = {
        "size": 15,
        "_source": {
            "exclude": [
                "vector"
            ]
        },
        "query": {
                    "knn": {
                    "vector": {
                        "vector": vector,
                        "k": 15
                    }
                }
            }
        }
        search_result = self.client.search(index=index, body=search_body)
        _score_list = []
        origin_text_list = []
        origin_question = []
        for s in search_result["hits"]["hits"]:
            _score_list.append(s['_score'])
            origin_question.append(s['_source']['origin-question'])
            origin_text_list.append(s['_source']['origin-text'])
        search_result_dict = {"score": _score_list, "origin-question": origin_question, "origin-text": origin_text_list}
        return search_result_dict
    

    def hybrid_search(self, text, model_name, index, session_state) -> dict:
        vector = self.text_to_vector(text=text, model_name=model_name)
        search_body = {
            "size": 15,
            "_source": {
                "exclude": [
                "vector"
                ]
            },
            "query": {
                "hybrid": {
                "queries": [
                    {
                    "match": {
                        "origin-question": {
                        "query": text
                        }
                    }
                    },
                    {
                    "match": {
                        "origin_text": {
                        "query": text
                        }
                    }
                    },
                    {
                    "knn": {
                        "vector": {
                        "vector": vector,
                        "k": 15
                        }
                    }
                    }
                ]
                }
            },
            "search_pipeline" : {
                "phase_results_processors": [
                {
                    "normalization-processor": {
                    "normalization": {
                        "technique": "min_max"
                    },
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                        "weights": [
                            session_state["weight1"],
                            session_state["weight2"],
                            session_state["weight3"]
                        ]
                        }
                    }
                    }
                }
                ]
            }
            }
        search_result = self.client.search(index=index, body=search_body)
        _score_list = []
        origin_text_list = []
        origin_question = []
        for s in search_result["hits"]["hits"]:
            _score_list.append(s['_score'])
            origin_question.append(s['_source']['origin-question'])
            origin_text_list.append(s['_source']['origin-text'])
        search_result_dict = {"score": _score_list, "origin-question": origin_question, "origin-text": origin_text_list}
        return search_result_dict
    

    def completion_hybrid_search(self, text, model_name, index, session_state) -> dict:
        vector = self.text_to_vector(text=text, model_name=model_name)
        search_body = {
            "size": 15,
            "_source": {
                "exclude": [
                "vector"
                ]
            },
            "query": {
                "hybrid": {
                "queries": [
                    {
                    "match": {
                        "origin_text": {
                        "query": text
                        }
                    }
                    },
                    {
                    "knn": {
                        "vector": {
                        "vector": vector,
                        "k": 15
                        }
                    }
                    }
                ]
                }
            },
            "search_pipeline" : {
                "phase_results_processors": [
                {
                    "normalization-processor": {
                    "normalization": {
                        "technique": "min_max"
                    },
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                        "weights": [
                            session_state["weight2"],
                            session_state["weight3"]
                        ]
                        }
                    }
                    }
                }
                ]
            }
            }
        search_result = self.client.search(index=index, body=search_body)
        _score_list = []
        origin_text_list = []
        origin_question = []
        for s in search_result["hits"]["hits"]:
            _score_list.append(s['_score'])
            origin_question.append(s['_source']['origin-question'])
            origin_text_list.append(s['_source']['origin-text'])
        search_result_dict = {"score": _score_list, "origin-question": origin_question, "origin-text": origin_text_list}
        return search_result_dict
    

    def question_hybrid_search(self, text, model_name, index, session_state) -> dict:
        vector = self.text_to_vector(text=text, model_name=model_name)
        search_body = {
            "size": 15,
            "_source": {
                "exclude": [
                "vector"
                ]
            },
            "query": {
                "hybrid": {
                "queries": [
                    {
                    "match": {
                        "origin-question": {
                        "query": text
                        }
                    }
                    },
                    {
                    "knn": {
                        "vector": {
                        "vector": vector,
                        "k": 15
                        }
                    }
                    }
                ]
                }
            },
            "search_pipeline" : {
                "phase_results_processors": [
                {
                    "normalization-processor": {
                    "normalization": {
                        "technique": "min_max"
                    },
                    "combination": {
                        "technique": "arithmetic_mean",
                        "parameters": {
                        "weights": [
                            session_state["weight1"],
                            session_state["weight3"]
                        ]
                        }
                    }
                    }
                }
                ]
            }
            }
        search_result = self.client.search(index=index, body=search_body)
        _score_list = []
        origin_text_list = []
        origin_question = []
        for s in search_result["hits"]["hits"]:
            _score_list.append(s['_score'])
            origin_question.append(s['_source']['origin-question'])
            origin_text_list.append(s['_source']['origin-text'])
        search_result_dict = {"score": _score_list, "origin-question": origin_question, "origin-text": origin_text_list}
        return search_result_dict
    

    def text_search_question(self, text, index) -> dict:
        search_body = {
        "size": 15,
        "_source": {
            "exclude": [
                "vector"
            ]
        },
        "query": {
                "match": {
                "origin-question": text
                }
            }
        }
        search_result = self.client.search(index=index, body=search_body)
        _score_list = []
        origin_text_list = []
        origin_question = []
        for s in search_result["hits"]["hits"]:
            _score_list.append(s['_score'])
            origin_question.append(s['_source']['origin-question'])
            origin_text_list.append(s['_source']['origin-text'])
        search_result_dict = {"score": _score_list, "origin-question": origin_question, "origin-text": origin_text_list}
        return search_result_dict
    
    def text_search_completion(self, text, index) -> dict:
        search_body = {
        "size": 15,
        "_source": {
            "exclude": [
                "vector"
            ]
        },
        "query": {
                "match": {
                "origin-text": text
                }
            }
        }
        search_result = self.client.search(index=index, body=search_body)
        _score_list = []
        origin_text_list = []
        origin_question = []
        for s in search_result["hits"]["hits"]:
            _score_list.append(s['_score'])
            origin_question.append(s['_source']['origin-question'])
            origin_text_list.append(s['_source']['origin-text'])
        search_result_dict = {"score": _score_list, "origin-question": origin_question, "origin-text": origin_text_list}
        return search_result_dict

class ExtendedEnum(Enum):

    @classmethod
    def list(cls):
        return [c.value for c in cls]

class HNSW_Search(ExtendedEnum):
    NORMAL_SEARCH = "Normal_Vector_Search"
    HYBRID_SEARCH = "Hybrid_Search"
    HYBRID_SEARCH_QUESTION = "Question_Hybrid_Search"
    HYBRID_SEARCH_COMPLETION = "Completion_Hybrid_Search"
    TEXT_SEARCH_QUESTION = "Question_Text_Search"
    TEXT_SEARCH_COMPLETION = "Completion_Text_Search"