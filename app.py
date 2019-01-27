from riotpy import *
from flask import jsonify
# to run on windows...
'''
set FLASK_APP=app
set FLASK_DEBUG=1
python -m flask run -h 0.0.0.0 -p 5000
'''


#--------------------------------
# functions
def list_files_from_dir(path):
    '''list files from path and send it '''
    import os
    if not os.path.isdir(path):
        return []
    files = [path + f for f in os.listdir(path)]
    return files


# --------------------  download traits -----------------------
def obo_to_df(obofile):
    import obo, pandas as pd
    obolines = (line.decode('utf-8') for line in obofile)
    graph = obo.read_obo(obolines)
    data = []
    for val in graph.node.values():
        if type(val) == dict:
            if 'attr_dict' in val.keys():
                if 'name' in val['attr_dict'].keys():
                    data.append(val['attr_dict'])
            
    df = pd.DataFrame(data)
    return df

def download_traits(url = 'https://raw.githubusercontent.com/Planteome/plant-trait-ontology/master/to.obo', use_cache = True):
    import pandas as pd
    fname = 'trait_onthology.csv'
    if not (os.path.isfile(fname) and use_cache):
        import urllib, obo, pandas as pd
        with urllib.request.urlopen(url) as obofile:
            df = obo_to_df(obofile)
            df.to_csv(fname, index=False)
    return pd.read_csv(fname)




# =====================     RIOTPY   ===========================================

#--------------------------------
# riotpy tags
class maintag(RiotTag):
    def HTML(self):
        h2('hello riotpy!', class_='green-text')()
        with row():
            with col('s3 green white-text', style='overflow:auto;'):
                h6('List of images')()
                with a(each='{im in images}',
                       onclick='{image_clicked}',
                       class_='white-text orange truncate',
                       style='width:100%; float:left; cursor:pointer;'):
                    content('{im}')
                
                # list of ontologies
                h6('the ontologies')()
                with div(style='height:300px; overflow:auto;'):
                    with div(each='{o in ontologies}'):
                        div(content='{o.name}', class_='white blue-text')()
            
            with col('s9 orange white-text'):
                h6('The image!')()
                img(src='{image}', style='width:100%')()
                

    
    def JS(self):
        '''functions here turn into JavaScript !!!! '''
        @on("mount")
        def mount():
            me.load_images()
            me.load_ontologies()
        
        @make_self
        def load_images():
            def images_loaded(res):
                me.images = eval(res.currentTarget.response)
                me.update()
                window.maintag = me # for testing: show the content of the tag in the global window object
            #ajax call
            xhr = XMLHttpRequest()
            xhr.open('GET', 'list_files_from_paths/images/')
            xhr.onload = images_loaded
            xhr.send()
        
        @make_self
        def load_ontologies():
            def onto_loaded(res):
                me.ontologies = eval(res.currentTarget.response)
                me.update()
                window.maintag = me # for testing: show the content of the tag in the global window object
            #ajax call
            xhr = XMLHttpRequest()
            xhr.open('GET', 'get_trait_ontologies')
            xhr.onload = onto_loaded
            xhr.send()

        @make_self
        def image_clicked(e):
            me.image = e.target.innerHTML
            me.update()


#--------------------------------
# riotpy application
app = RiotPyApp(toptitle="Hi riotpy!").app

#--------------------------------
# Rest API
@app.route('/list_files_from_paths/<path:path>')
def list_files_from_paths(path):
    files = list_files_from_dir(path)
    return jsonify(files)


@app.route('/get_trait_ontologies/')
def get_trait_ontologies():
    ontologies = download_traits()
    return jsonify(ontologies.to_dict(orient='records'))