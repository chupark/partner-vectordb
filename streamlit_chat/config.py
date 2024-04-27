import os

NCP_CONFIG = {
   'ACCESS_KEY': os.environ.get('NCP_ACCESS_KEY', None),
   'SECRET_KEY': os.environ.get('NCP_SECRET_KEY', None)
}


HCX_EMBEDDING = {
    'APP_ID': os.environ.get('EMB_APP_ID'),
    'X-NCP-CLOVASTUDIO-API-KEY': os.environ.get('X_NCP_CLOVASTUDIO_API_KEY', None),
    'X-NCP-APIGW-API-KEY': os.environ.get('X_NCP_APIGW_API_KEY', None)
}

OPENSEARCH = {
    'HOST' : os.environ.get('OSH_HOST', None), 
    'ID': os.environ.get('OSH_ID', None),
    'PASSWD' : os.environ.get('OSH_PW', None)
}