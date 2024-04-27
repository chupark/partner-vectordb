import streamlit as st

from modules.OpenSearch import OpenSearchHelper

def refresh():
    st.rerun()

prefix = "ncp_edu_"
st.sidebar.header("Index Config")
st.sidebar.button("새로고침", type="primary", on_click=refresh)
st.session_state["dimension"] = st.sidebar.number_input(
    label="dimension",
    min_value=0,
    max_value=10000,
    value=1024
)

st.session_state["space_type"] = st.sidebar.selectbox(
    label="space_type",
    placeholder="Choose an option",
    options=("l2", "innerproduct", "cosinesimil", "l1", "linf")
)

st.session_state["ef_search"] = st.sidebar.number_input(
    label="ef_search",
    min_value=0,
    max_value=10000,
    value=512
)

st.session_state["ef_construction"] = st.sidebar.number_input(
    label="ef_construction",
    min_value=0,
    max_value=10000,
    value=512
)

st.session_state["m"] = st.sidebar.slider(
    label="m",
    min_value=2,
    max_value=100,
    value=16
)

st.session_state["index_name"] = st.sidebar.text_input(
    label="index_name",
    value=f"sc2-vector"
)

st.session_state["embedding_model_name"] = st.sidebar.text_input(
    label="embedding_model_name",
    value="clir-sts-dolphin"
)





opensearch = OpenSearchHelper()

def call_create_index():
    opensearch.create_index(session_sate=st.session_state)

def load_sc2_csv():
    opensearch.load_sc2_data(session_state=st.session_state)

st.sidebar.button("Index 생성하기", type="primary", on_click=call_create_index)
 
st.session_state['indices'] = opensearch.get_indices(prefix=prefix)
for i in st.session_state['indices']:
    with st.form(i):
        _emb_model_name = ""
        if st.session_state['indices'][i]['mappings']['properties']['vector']['type'] != "knn_vector":
            continue
        for j in st.session_state['indices'][i]['mappings']['properties']:
            if str(j).startswith("emb-model--"):
                _emb_model_name = (str(j).split("--"))[1]
        _dimension = st.session_state['indices'][i]['mappings']['properties']['vector']['dimension']
        _ef_search = st.session_state['indices'][i]['settings']['index']['knn.algo_param']['ef_search']
        _engine = st.session_state['indices'][i]['mappings']['properties']['vector']['method']['engine']
        _space_type = st.session_state['indices'][i]['mappings']['properties']['vector']['method']['space_type']
        _name = st.session_state['indices'][i]['mappings']['properties']['vector']['method']['name']
        _ef_constructnion = st.session_state['indices'][i]['mappings']['properties']['vector']['method']['parameters']['ef_construction']
        _m = st.session_state['indices'][i]['mappings']['properties']['vector']['method']['parameters']['m']
        _doc_cnt = opensearch.get_document_count(i)
        st.markdown(f"### {i}")
        st.markdown(f"#### Total Docs : {_doc_cnt['count']}")
        st.markdown(f"#### Embedding Model : {_emb_model_name}")
        st.markdown(f"""
| lib | engine | dimension | space | ef_search | ef_constructnion | m | 
| :------ | :------ | :------ | :------| :-----| :---------| :---------| 
| {_name} | {_engine} | {_dimension} | {_space_type} | {_ef_search} | {_ef_constructnion} | {_m} |
""")
        st.json(st.session_state['indices'][i], expanded=False)

        # Every form must have a submit button.
        submitted2 = st.form_submit_button("Insert")
        submitted = st.form_submit_button("Delete", type="primary")
        if submitted:
            opensearch.delete_index(index = i)
            st.rerun()
        if submitted2:
            opensearch.load_sc2_data(index = i, session_state=st.session_state)
            st.rerun()