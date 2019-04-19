

import sqlite3




class DBConn(object):
    def __init__(self, db_path, use_row=True):
        """ Sets up Database connection and loads in the spatialite extension """
        self.conn = sqlite3.connect(db_path, check_same_thread=False,)
        self.conn.enable_load_extension(True)
        self.conn.execute('SELECT load_extension("mod_spatialite")')
        self.conn.row_factory = sqlite3.Row if use_row else dict_factory


def upload_points(db_path, point_path, table_name='concave'):
    db = DBConn(db_path)
    
