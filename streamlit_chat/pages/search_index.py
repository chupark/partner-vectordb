import streamlit as st
import pandas as pd
from modules.OpenSearch import OpenSearchHelper
from modules.OpenSearch import HNSW_Search
from modules.StreamlitWidget import Slider_label_visiability

prefix = "ncp_edu_"
opensearch = OpenSearchHelper()
st.session_state["hybrid_weight_visiability"] = Slider_label_visiability.HIDDEN.value
st.session_state['indices'] = opensearch.get_indices(prefix=prefix)



indices = tuple([i for i in st.session_state['indices']])

st.session_state["search_index"] = st.sidebar.selectbox(
    label="index",
    options=indices
)

st.session_state["search_method"] = st.sidebar.selectbox(
    label="검색방법",
    options=tuple(HNSW_Search.list())
)

if st.session_state["search_method"] == HNSW_Search.HYBRID_SEARCH.value:
    st.session_state["weight1"] = st.sidebar.number_input(
        label="질문 필드 비중",
        min_value=0.0,
        max_value=1.0,
        value=0.2
    )
    st.session_state["weight2"] = st.sidebar.number_input(
        label="답변 필드 비중",
        min_value=0.0,
        max_value=1.0,
        value=0.1
    )
    st.session_state["weight3"] = st.sidebar.number_input(
        label="벡터 필드 비중",
        min_value=0.0,
        max_value=1.0,
        value=0.7
    )
elif st.session_state["search_method"] == HNSW_Search.HYBRID_SEARCH_QUESTION.value:
    st.session_state["weight1"] = st.sidebar.number_input(
        label="질문 필드 비중",
        min_value=0.0,
        max_value=1.0,
        value=0.2
    )
    st.session_state["weight3"] = st.sidebar.number_input(
        label="벡터 필드 비중",
        min_value=0.0,
        max_value=1.0,
        value=0.8
    )
elif st.session_state["search_method"] == HNSW_Search.HYBRID_SEARCH_COMPLETION.value:
    st.session_state["weight2"] = st.sidebar.number_input(
        label="답변 필드 비중",
        min_value=0.0,
        max_value=1.0,
        value=0.2
    )
    st.session_state["weight3"] = st.sidebar.number_input(
        label="벡터 필드 비중",
        min_value=0.0,
        max_value=1.0,
        value=0.8
    )

st.session_state["embedding_model"] = ""

with st.container(border=True) as container :
    selected_index = st.session_state['indices'][st.session_state["search_index"]]
    if selected_index['mappings']['properties']['vector']['type'] != "knn_vector":
        None
    _emb_model_name = ""
    for j in selected_index['mappings']['properties']:
        if str(j).startswith("emb-model--"):
            _emb_model_name = (str(j).split("--"))[1]
            st.session_state["embedding_model"] = _emb_model_name
    _dimension = selected_index['mappings']['properties']['vector']['dimension']
    _ef_search = selected_index['settings']['index']['knn.algo_param']['ef_search']
    _engine = selected_index['mappings']['properties']['vector']['method']['engine']
    _space_type = selected_index['mappings']['properties']['vector']['method']['space_type']
    _name = selected_index['mappings']['properties']['vector']['method']['name']
    _ef_constructnion = selected_index['mappings']['properties']['vector']['method']['parameters']['ef_construction']
    _m = selected_index['mappings']['properties']['vector']['method']['parameters']['m']
    _doc_cnt = opensearch.get_document_count(st.session_state["search_index"])
    st.markdown(f"### {st.session_state['search_index']}")
    st.markdown(f"#### Total Docs : {_doc_cnt['count']}")
    st.markdown(f"#### Embedding Model : {_emb_model_name}")
    st.markdown(f"""
| lib | engine | dimension | space | ef_search | ef_constructnion | m | 
| :------ | :------ | :------ | :------| :-----| :---------| :---------| 
| {_name} | {_engine} | {_dimension} | {_space_type} | {_ef_search} | {_ef_constructnion} | {_m} |
""")
    st.markdown("")

if prompt := st.chat_input("What is up?"):
    with st.chat_message("user"):
        prompt
        res = {}
        if st.session_state["search_method"] == HNSW_Search.NORMAL_SEARCH.value:
            res = opensearch.normal_search(text=prompt, model_name=st.session_state["embedding_model"], index=st.session_state["search_index"])

        elif st.session_state["search_method"] == HNSW_Search.HYBRID_SEARCH.value:
            if (st.session_state["weight1"] + st.session_state["weight2"] + st.session_state["weight3"] == 1):
                res = opensearch.hybrid_search(text=prompt, model_name=st.session_state["embedding_model"], index=st.session_state["search_index"], session_state=st.session_state)
            else :
                st.markdown("비중의 합은 1이어야 합니다.")

        elif st.session_state["search_method"] == HNSW_Search.TEXT_SEARCH_QUESTION.value:
            res = opensearch.text_search_question(text=prompt, index=st.session_state["search_index"])

        elif st.session_state["search_method"] == HNSW_Search.TEXT_SEARCH_COMPLETION.value:
            res = opensearch.text_search_completion(text=prompt, index=st.session_state["search_index"])

        elif st.session_state["search_method"] == HNSW_Search.HYBRID_SEARCH_QUESTION.value:
            if (st.session_state["weight1"] + st.session_state["weight3"] == 1):
                res = opensearch.question_hybrid_search(text=prompt, model_name=st.session_state["embedding_model"], index=st.session_state["search_index"], session_state=st.session_state)
            else :
                st.markdown("비중의 합은 1이어야 합니다.")
                
        elif st.session_state["search_method"] == HNSW_Search.HYBRID_SEARCH_COMPLETION.value:
            if (st.session_state["weight2"] + st.session_state["weight3"] == 1):
                res = opensearch.completion_hybrid_search(text=prompt, model_name=st.session_state["embedding_model"], index=st.session_state["search_index"], session_state=st.session_state)
            else :
                st.markdown("비중의 합은 1이어야 합니다.")
            
        
        df = pd.DataFrame(res)
        st.table(df)

