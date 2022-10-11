import logging
from re import S
from bot.db.DBConnection import DBConnection
from bot.db.DBManager import DBManager

from util.constants import DbConstants
from util.generate_hash import get_int32_hash
from .db import db, transaction_manager
from typing import Any
from zope.generations.generations import generations_key
import transaction

from util.exceptions import TreeReferencedDoesNotExist

log = logging.getLogger(__name__)

# last version: conn: Optional[ZODB.connection] = None


class DBUtil:
    """! Database utility class for inserting, updating and deleting DB records."""
    conn = DBConnection.connection

    def __init__(self) -> None:
        pass

    @staticmethod
    def get_db_ref():
        """! Getter method for the DB reference.
        @return ZODB.DB object
        """
        return db

    @staticmethod
    def get_current_db_generation():
        """! Getter method for the DB upgrade generation.
        @param conn optional DB connection
        @return int
        """
        return DBUtil.conn.root()[generations_key][DbConstants.DB_APP_NAME]

    ###############################################
    # Get, Insert, Update and Delete methods.     #
    ###############################################

    @staticmethod
    def get_record(tree_name: str, uuid: int):
        """! Get method for records in the DB.
        @param tree_name name of the OOBTree tree for the record
        @param uuid unique id of the record
        @return record if found, None otherwise
        """
        if not DBUtil.conn:
            DBUtil.conn = db.open()
        return DBUtil.conn.root()[tree_name].get(uuid)

    @staticmethod
    def insert_record(tree_name: str, uuid: int, object: Any):
        """! Insert method for records into DB.
        @param tree_name name of the OOBTree tree for the record to be inserted into
        @param uuid unique id of the record for later reference
        @param object data for the record 
        @return 1 if the item was inserted, or 0 otherwise
        """
        if not DBUtil.conn:
            DBUtil.conn = db.open()
        # transaction.begin()
        DBUtil.conn.root()[tree_name].insert(uuid, object)
        transaction.commit()

    @staticmethod
    def insert_or_update_record(tree_name: str, uuid: int, object: Any):
        """! Insert or update method for records in the DB.
        @param tree_name name of the OOBTree tree for the record
        @param uuid unique id of the record or -1 if first found
        @param object data for the record 
        @return 1 if record added, 0 if not updated or not found
        """
        if not DBUtil.conn:
            DBUtil.conn = db.open()
        if DBManager.tree_exists(tree_name):
            if uuid == -1:
                if len(DBUtil.conn.root()[tree_name].values()) == 0:
                    # no records exist in the tree
                    return 0
                # update the last record
                DBUtil.conn.root()[tree_name].values()[-1] = object
                return 1

            if DBUtil.get_record(tree_name, uuid) == 0:
                # specific uuid not found as a key in the tree
                DBUtil.insert_record(tree_name, uuid, object)
                return 0
            else:
                # key found and value updated
                DBUtil.conn.root()[tree_name][uuid] = object
                transaction.commit()
                return 1
        else:
            log.warn(
                f'Tree {tree_name} does not exist. No error thrown because it\'s an update of a record.')
            return 0

    @staticmethod
    def update_record(tree_name: str, uuid: int, object: Any):
        """! Update method for records in the DB.
        @param tree_name name of the OOBTree tree for the record
        @param uuid unique id of the record
        @param object data for the record 
        @return 1 if record added, 0 if not updated or not found
        """

        if (DBManager.tree_exists(tree_name)):
            # update record if it exists
            record = DBUtil.get_record(tree_name, uuid)
            if not record:
                log.warn(f"Record in tree [{tree_name}] with uuid [{uuid}] does not exist. No error thrown because it\'s an update of a record. Inserting record instead ...")            
                DBUtil.insert_or_update_record(tree_name, uuid, object)
                return 0
            
            DBUtil.conn.root()[tree_name][uuid] = object
            transaction.commit()

            log.info(f"Updating object: {object} uuid: {uuid} in tree {tree_name}")
            return 1
        else:
            log.warn(
                f'Tree {tree_name} does not exist. No error thrown because it\'s an update of a record.')
            return 0

    @staticmethod
    def delete_record(tree_name: str, uuid: int):
        """! Delete method marks record as active = False and thereby ready for later deletion from DB.
        @param tree_name name of the OOBTree tree for the record to be inserted into
        @param uuid unique id of the record 
        @return None
        """

        DBUtil.conn.root()[tree_name].get(uuid).active = False
        transaction.commit()

    ###############################################
    # General getters.                            #
    ###############################################
    @staticmethod
    def _get_objects_from_tree(tree_name: str):
        """! Get all objects unfiltered from a tree."""
        if not DBManager.tree_exists(tree_name):
            raise TreeReferencedDoesNotExist(
                f'Referenced tree: {tree_name} does not exist!')
        return DBUtil.conn.root()[tree_name].values()

    @staticmethod
    def get_all(tree_name: str, **kwargs):
        """! Get all objects from a tree."""
        if not DBUtil.conn:
            DBUtil.conn = db.open()
        all_objs = DBUtil._get_objects_from_tree(tree_name)

        if kwargs:
            result = []
            for k, v in kwargs.items():
                for obj in all_objs:
                    if obj[k] == v and obj['active'] == True:
                        result.append(obj)

        return all_objs

    @staticmethod
    def get_account_address_from_telegram_user_id(telegram_user_id: int):
        """! Returns account_address string of the Telegram user if the user is an owner else it returns None."""
        owner = DBUtil.get_owner(telegram_user_id)

        if not owner:
            return None
        return owner.get_account_address()
    ###############################################
    # Object getters.                             #
    ###############################################

    @staticmethod
    def get_users():
        """! Get all users from tree.
        @return all User type objects
        """
        return DBUtil.get_all(DbConstants.TREE_USERS)

    @staticmethod
    def get_owners():
        """! Get all owners from tree.
        @return all User type objects
        """
        return DBUtil.get_all(DbConstants.TREE_OWNERS)

    @staticmethod
    def get_owner(telegram_user_id: int):
        """! Get an owner from tree.
        @return User type object
        """
        query = DBUtil.get_all(DbConstants.TREE_OWNERS, telegram_user_id=telegram_user_id)
        if len(query)==0:
            return None
        return query[0]
    
    @staticmethod
    def get_hotspots():
        """! Get all hotspots from tree.
        @return all Hotspot type objects
        """
        return DBUtil.get_all(DbConstants.TREE_HOTSPOTS)

    @staticmethod
    def get_hotspots_by_owner(account_address: str):
        """! Get all hotspots for an owner from tree.
        @return all Hotspot type objects for an owner
        """
        query = DBUtil.get_all(DbConstants.TREE_HOTSPOTS, account_address=account_address)
        if len(query)==0:
            return None
        return query

    @staticmethod
    def get_activities_by_owner(account_address):
        """! Get all activities for an owner from tree.
        @return all Activity type objects for a certain owner
        """
        return DBUtil.get_all(DbConstants.TREE_ACTIVITIES, account_address=account_address)

    @staticmethod
    def get_menus_by_user(telegram_user_id: int):
        """! Get all menus from a tree for specific user.
        @return all MenuNode type objects
        """
        return DBUtil.get_all(DbConstants.TREE_MENU_NODES, telegram_user_id=telegram_user_id)

    @staticmethod
    def get_menu_manager_for_user(telegram_user_id: int):
        """! Get menu manager for specific user.
        @return all MenuNode type objects
        """
        query = DBUtil.get_record(DbConstants.TREE_MENU_MANAGERS, telegram_user_id)
        return query

    @staticmethod
    def get_owner_by_telegram_id(telegram_user_id: int):
        """! Get owner record by specifying Telegram user ID."""
        return DBUtil.get_all(DbConstants.TREE_OWNERS, telegram_user_id=telegram_user_id)[0]

    @staticmethod
    def get_bots():
        """! Get all bots from tree.
        @return all BotInstance type objects
        """
        return DBUtil.get_all(DbConstants.TREE_BOT_INSTANCE)

    @staticmethod
    def get_bot_for_user(telegram_user_id: int):
        """! Returns Bot type object. """
        query = DBUtil.get_record(DbConstants.TREE_BOT_INSTANCE, telegram_user_id)
        return query

    @staticmethod
    def is_bot_active(telegram_user_id: int) -> bool:
        """! Returns Bot.active field value. """
        instance = DBUtil.get_bot_for_user(telegram_user_id)
        if not instance:
            return False
        return instance.active

    @staticmethod
    def deactivate_bot_for_user(telegram_user_id: int) -> bool:
        """! Sets Bot.active field value to False. """
        instance = DBUtil.get_bot_for_user(telegram_user_id)
        if instance:
            instance.active = False
            DBUtil.insert_or_update_record(
                tree_name=DbConstants.TREE_BOT_INSTANCE, uuid=instance.uuid, object=instance)
        else:
            log.warn(
                f'BotInstance for telegram_user_id {telegram_user_id} was not found while deactivating!')

    @staticmethod
    def activate_bot_for_user(telegram_user_id: int) -> bool:
        """! Sets Bot.active field value to True. """
        instance = DBUtil.get_bot_for_user(telegram_user_id)
        if instance:
            instance.active = True
            DBUtil.insert_or_update_record(DbConstants.TREE_BOT_INSTANCE, telegram_user_id, instance)
        else:
            log.warn(
                f'BotInstance for telegram_user_id {telegram_user_id} was not found while activating!')

    ###############################################
    # Other methods for objects                   #
    ###############################################

    @staticmethod
    def is_in_db(tree_name: str, uuid: int):
        """! Check if an uuid exists in all trees."""
        if not DBManager.tree_exists(tree_name):
            raise TreeReferencedDoesNotExist(
                f'Referenced tree: {tree_name} does not exist!')

        return True if DBUtil.conn.root()[tree_name].get(uuid) else False

    @staticmethod
    def is_user_registered(telegram_user_id: str) -> bool:
        """! Check if user has registered an account with the bot.
        An account includes giving Helium account address and the bot will automatically assign jobs and notifications for registered hotspots.
        """
        if not DBUtil.exists_user(telegram_user_id):
            return False
        
        user = DBUtil.get_record(DbConstants.TREE_USERS, telegram_user_id)
        if user:
            return user.is_registered
        else:
            log.warn(f'User is not found while checking if registered!')
            return False

    @staticmethod
    def exists_hotspot(hotspot_address: str):
        query = DBUtil.get_all(DbConstants.TREE_HOTSPOTS, hotspot_address=hotspot_address)
        if len(query)==0:
            return False
        else:
            return True

    @staticmethod
    def exists_user(telegram_user_id: str):
        query = DBUtil.get_all(DbConstants.TREE_USERS, telegram_user_id=telegram_user_id)
        if len(query)==0:
            return False
        else:
            return True

    @staticmethod
    def get_stats():
        """! Display for each tree the number of records. """
        import os, json
        from .db import __location__
        with open(os.path.join(__location__, 'trees.json'), 'r') as f:
            trees = json.load(f)
        # loop through tree names in json and create OOBTrees for each of them
        if not DBUtil.conn:
            DBUtil.conn = DBUtil.get_db_ref().open()
        for tree in trees['trees']: 
            msg = f"{tree['name']} contains {len(DBUtil.conn.root()[tree['name']])} objects."
            log.info(msg)
            print(msg)