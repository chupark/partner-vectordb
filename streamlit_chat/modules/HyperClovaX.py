
import httpx
import logging

logging.basicConfig(
    format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.WARN
)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARN)


class HyperClovaX():
    def __init__(self, clova_studio_api_key: str, apigw_api_key: str):
        self.X_NCP_CLOVASTUDIO_API_KEY = clova_studio_api_key
        self.X_NCP_APIGW_API_KEY = apigw_api_key
        
        self.emb_appId = ""
        self.emb_model_name = ""

    def tokenizer(self, model_name):
        token = ""
        return token
    
    def set_embedding(self, app_id: str, model_name: str) -> None :
        self.emb_appId = app_id
        self.emb_model_name = model_name

    def embedding(self, text):
        base_url = "https://clovastudio.apigw.ntruss.com"
        endpoint = f"/testapp/v1/api-tools/embedding/{self.emb_model_name}/{self.emb_appId}"
        url = base_url + endpoint

        headers = {
            "Content-Type": "application/json",
            "X-NCP-CLOVASTUDIO-API-KEY": self.X_NCP_CLOVASTUDIO_API_KEY,
            "X-NCP-APIGW-API-KEY": self.X_NCP_APIGW_API_KEY
        }

        body = {
            "text": text
        }

        res = httpx.post(url=url, headers=headers, json=body)
        return res