from enum import Enum
from FlagEmbedding import BGEM3FlagModel
model = BGEM3FlagModel('BAAI/bge-m3',  use_fp16=True) # Setting use_fp16 to True speeds up computation with a slight performance degradation

class ExtendedEnum(Enum):

    @classmethod
    def list(cls):
        return [c.value for c in cls]

class EmbeddingModels(ExtendedEnum):
    HCX_STS_DOLPHIN = "clir-sts-dolphin"
    HCX_EMB_DOLPHIN = "clir-emb-dolphin"
    BGE_M3 = "BGE_M3"
    # BGE_M3_LEXICAL = "BGE_M3-lexical_weights"
    # BGE_M3_COLBERT = "BGE_M3-colbert_vecs"


class BGME3_EMB():
    def __init__(self, encoding: str):
        self.full_encoding = encoding
        # self.encoding = self.setEncoding(encoding=encoding)

    # def setEncoding(self, encoding: str):
    #     return (encoding.split("-"))[1]
    
    def do_embeding(self, text: str):
        encoded_text = []
        if self.full_encoding == EmbeddingModels.BGE_M3.value:
            encoded_text = model.encode(sentences=[text], batch_size=12, max_length=2048, return_dense=True, return_sparse=False, return_colbert_vecs=False)['dense_vecs']
        # elif self.full_encoding == EmbeddingModels.BGE_M3_DENSE.value:
        #     encoded_text = model.encode(sentences=[text], batch_size=12, max_length=2048, return_dense=True, return_sparse=True, return_colbert_vecs=False)
        # elif self.full_encoding == EmbeddingModels.BGE_M3_DENSE.value:
        #     encoded_text = model.encode(sentences=[text], batch_size=12, max_length=2048, return_dense=True, return_sparse=False, return_colbert_vecs=True)
        return encoded_text[0]