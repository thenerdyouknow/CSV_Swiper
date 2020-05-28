import tornado.httpserver, tornado.ioloop, tornado.options, tornado.web, os.path, random, string
from tornado.options import define, options
import csv
import pandas as pd
import ast
import sys

define("port", default=8000, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", IndexHandler),
            (r"/upload", UploadHandler),
            (r"/app",ApplicationHandler)
        ]
        cookie_secret = "AjOIgQb2JyOv5c6TIwUYKuu4HFerEedgAfTZ1yCc0/kL2ryBf9xCtoKGnwQ1uN3uuVc="
        template_path = os.path.join(os.path.dirname( __file__) ,"templates")
        static_path = os.path.join(os.path.dirname( __file__) ,"static")
        tornado.web.Application.__init__(self, handlers,cookie_secret=cookie_secret,template_path=template_path,static_path=static_path,ui_modules={'package_includes': PackagesIncludeModule},)


#------------MODULES------------
class PackagesIncludeModule(tornado.web.UIModule):
    def render(self):
        return self.render_string("modules/packages_includes.html")
#------------MODULES------------

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("upload_form.html",error="")

class UploadHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.clear_all_cookies("/")

    def post(self):
        file = self.request.files['input_file'][0]
        show_columns = self.get_argument('show_columns').split(",")
        save_columns = self.get_argument('save_columns').split(",")
        
        try:
            os.mkdir("uploads")
        except FileExistsError:
            pass

        filename = 'uploads/'+file['filename']
        with open(filename,'wb') as open_file:
            open_file.write(file['body'])
            self.set_secure_cookie("filepath",filename)

        self.set_secure_cookie("show_columns",str(show_columns))
        self.set_secure_cookie("save_columns",str(save_columns))

        self.redirect('/app')
        return

class ApplicationHandler(tornado.web.RequestHandler):

    def initialize(self):
        FOLDER_NAME = 'sorted'
        AFFIRMATIVE = 'affirmative.csv'
        NEGATIVE = 'negative.csv'
        df_filepath = self.get_secure_cookie("filepath").decode()
        save_columns = ast.literal_eval(self.get_secure_cookie("save_columns").decode())
        base_filepath = os.path.join(FOLDER_NAME,df_filepath.split(".")[0].split("/")[-1])

        try:
            os.mkdir(FOLDER_NAME)
        except FileExistsError:
            pass

        try:
            os.mkdir(base_filepath)
        except FileExistsError:
            return

        open_file_affirmative = open(os.path.join(base_filepath,AFFIRMATIVE),'w')
        open_file_negative = open(os.path.join(base_filepath,NEGATIVE),'w')

        csv_writer_affirmative = csv.writer(open_file_affirmative,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer_negative = csv.writer(open_file_negative,delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)      

        try:
            df = pd.read_csv(df_filepath)
            self.set_secure_cookie("length",str(df.shape[0]))
            if(save_columns[0]==''):
                df_columns = list(df.columns)
                csv_writer_affirmative.writerow(df_columns)
                csv_writer_negative.writerow(df_columns)
            else:
                csv_writer_affirmative.writerow(save_columns)
                csv_writer_negative.writerow(save_columns)
        except:
            err_type, error, traceback = sys.exc_info()
            self.render('error.html',error=error)

        open_file_affirmative.close()
        open_file_negative.close()        

        self.set_secure_cookie("affirmative",str(os.path.join(base_filepath,AFFIRMATIVE)))
        self.set_secure_cookie("negative",str(os.path.join(base_filepath,NEGATIVE)))
        return


    def get(self):

        df_filepath = self.get_secure_cookie("filepath").decode()
        show_columns = ast.literal_eval(self.get_secure_cookie("show_columns").decode())
        save_columns = ast.literal_eval(self.get_secure_cookie("save_columns").decode())

        try:
            self.index = int(self.get_secure_cookie("df_index").decode())
            self.index += 1
            self.set_secure_cookie("df_index",str(self.index))
        except AttributeError:
            self.set_secure_cookie("df_index","0")
            self.index = 0

        try:
            length = round((self.index/float(self.get_secure_cookie("length").decode()))*100,2)
        except:
            length = 0

        try:
            df = pd.read_csv(df_filepath)
            list_of_items = {}
            for each_column in show_columns:
                list_of_items[each_column.strip()] = df.iloc[self.index][each_column.strip()]
            self.render('app.html',column_data=list_of_items,error='',progress_width=length)

        except:
            err_type, error, traceback = sys.exc_info()
            self.render('error.html',error=error)

    def post(self):

        df_filepath = self.get_secure_cookie("filepath").decode()
        save_columns = ast.literal_eval(self.get_secure_cookie("save_columns").decode())
        self.index = int(self.get_secure_cookie("df_index").decode())

        try:
            df = pd.read_csv(df_filepath)
            list_of_items = {}

            if(save_columns[0]!=''):
                for each_column in save_columns:
                    list_of_items[each_column.strip()] = df.iloc[self.index][each_column.strip()]
            else:
                for each_column in list(df.columns):
                    list_of_items[each_column.strip()] = df.iloc[self.index][each_column.strip()]
        except:
            err_type, error, traceback = sys.exc_info()
            self.render('error.html',error=error)

        if self.get_argument('positive', None) is not None:
            with open(self.get_secure_cookie('affirmative').decode(),'a') as open_file:
                csv_writer = csv.writer(open_file)
                csv_writer.writerow(list(list_of_items.values()))

        elif self.get_argument('negative', None) is not None:
            with open(self.get_secure_cookie('negative').decode(),'a') as open_file:
                csv_writer = csv.writer(open_file)
                csv_writer.writerow(list(list_of_items.values()))

        self.redirect('/app')
        return
        

def main():
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()