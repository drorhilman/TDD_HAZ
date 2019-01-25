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
            
            with col('s9 orange white-text'):
                h6('The image!')()
                img(src='{image}', style='width:100%')()
    
    def JS(self):
        '''functions here turn into JavaScript !!!! '''
        @on("mount")
        def mount():
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