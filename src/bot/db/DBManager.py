import json
import os
import logging
from typing import Any, Optional
from zope.generations.generations import generations_key
import ZODB
from BTrees.OOBTree import OOBTree

log = logging.getLogger(__name__)
from .db import db, __location__
from util.constants import DbConstants

class DBManager():
    
    def init_db() -> None:
        """! Initialization method for the DB. This method inserts all OOBTree objects at the root of the ZODB database.
        @return None
        """
        DBManager._create_all_trees()
    
    @staticmethod
    def get_db_ref():
        """! Getter method for the DB reference.
        @return ZODB.DB object
        """
        return db

    @staticmethod
    def get_current_db_generation(conn: Optional[ZODB.connection] = None):
        """! Getter method for the DB upgrade generation.
        @param conn optional DB connection
        @return int
        """
        if not conn:
            conn = db.open()
        return conn.root()[generations_key][DbConstants.DB_APP_NAME] 

    
    ###############################################
    # Get, Insert, Update and Delete methods.     #
    ###############################################

    @staticmethod
    def get_record(tree_name: str, uuid: str, conn: Optional[ZODB.connection] = None):
        """! Get method for records in the DB.
        @param tree_name name of the OOBTree tree for the record
        @param uuid unique id of the record
        @return 1 if record found, 0 if not found 
        """
        if not conn:
            conn = db.open()
        return conn.root()[tree_name].get(uuid)
            
    @staticmethod
    def insert_record(tree_name: str, uuid: str, object: Any):
        """! Insert method for records into DB.
        @param tree_name name of the OOBTree tree for the record to be inserted into
        @param uuid unique id of the record for later reference
        @param object data for the record 
        @return 1 if the item was added, or 0 otherwise
        """
        with db.transaction() as connection:
            connection.root()[tree_name].insert(uuid, object)
    
    @staticmethod
    def update_record(tree_name: str, uuid: str, object: Any):
        """! Update method for records in the DB.
        @param tree_name name of the OOBTree tree for the record
        @param uuid unique id of the record
        @param object data for the record 
        @return 1 if record added, 0 if not updated or not found
        """
        if(DBManager.tree_exists(tree_name)):
            with db.transaction() as connection: 
                if(connection.root()[tree_name].get(uuid) == 0):
                    return 0
                else:
                    connection.root()[tree_name][uuid] = object
                    return 1
        else:
            print("this happens")
            return 0
    @staticmethod
    def delete_record(tree_name: str, uuid: str):
        """! Delete method marks record as active = False and thereby ready for later deletion from DB.
        @param tree_name name of the OOBTree tree for the record to be inserted into
        @param uuid unique id of the record 
        @return None
        """
        with db.transaction() as connection:
            connection.root()[tree_name].get(uuid).active = False
                
    ###############################################
    # Initalization methods for trees.            #
    ###############################################     
    
    @staticmethod
    def tree_exists(tree_name: str):
        """! Method that checks if given tree name exists in the DB.
        @param tree_name name of the OOBTree tree to be checked
        @return boolean
        """
        with db.transaction() as connection: 
            return tree_name in connection.root()

    @staticmethod
    def _create_tree(tree_name: str):
        """! Internal method for creating a tree with tree_name.
        @param tree_name name of the OOBTree tree to be created
        @return OOBTree inserted into DB named after tree_name parameter
        """
        if not DBManager.tree_exists(tree_name):    
            with db.transaction() as connection: 
                connection.root()[tree_name] = OOBTree()
                log.info('Created %s tree in the DB.', tree_name)
                return connection.root()[tree_name]    
    
    @staticmethod
    def _create_all_trees():
        """! Internal method for creating trees from trees JSON file.
        @return None
        """
        with open(os.path.join(__location__, 'trees.json'), 'r') as f:
            trees = json.load(f)
        # loop through tree names in json and create OOBTrees for each of them
        for tree in trees['trees']: 
            DBManager._create_tree(tree['name'])
        log.info('Finished tree structure creation in the DB.')
    
    ###############################################
    # Shortcut getter methods for trees.          #
    ###############################################
    
  
    @staticmethod
    def get_users_tree():
        """! Getter for 'users' tree.
        @return OOBTree named 'users'
        """ 
        if DBManager.tree_exists('users'):    
            with db.transaction() as connection: 
                return connection.root.users
        else:
            return DBManager._create_tree('users')

    @staticmethod
    def get_owners_tree():
        """! Getter for 'owners' tree.
        @return OOBTree named 'owners'
        """   
        if DBManager.tree_exists('owners'):    
            with db.transaction() as connection: 
                return connection.root.owners
        else:
            return DBManager._create_tree('owners')
      
    @staticmethod
    def get_hotspots_tree():
        """! Getter for 'hotspots' tree.
        @return OOBTree named 'hotspots'
        """  
        if DBManager.tree_exists('hotspots'):    
            with db.transaction() as connection: 
                return connection.root.hotspots
        else:
            return DBManager._create_tree('hotspots')
    
    @staticmethod
    def get_activities_tree():
        """! Getter for 'activities' tree.
        @return OOBTree named 'activities'
        """
        if DBManager.tree_exists('activities'):    
            with db.transaction() as connection: 
                return connection.root.activities
        else:
            return DBManager._create_tree('activities')
