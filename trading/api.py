import logging
import json
import threading
import time

from trading.constants import Headers
from trading.basic import Basic
from trading.models.connection_storage import ConnectionStorage
from trading.pb.trading_pb2 import (
    Credentials,
    Order,
    Update,
)
from typing import (
    List,
    Union,
)
from wrapt.decorators import synchronized
    
class API:
    """ Same operation then Basic but with "session_id" management. """

    @property
    def basic(self)->Basic:
        """ Getter for the attribute : self.basic
        
        Returns:
            {Basic} -- Current Basic object.
        """

        return self._basic

    @basic.setter
    def basic(self, basic:Basic):
        """ Setter for the attribute : self.basic

        Arguments:
            basic {Basic} -- New Basic object.
        """

        self._basic = basic
    
    
    @property
    def connection_storage(self)->Basic:
        """ Getter for the attribute : self.connection_storage
        
        Returns:
            {Basic} -- Current ConnectionStorage object.
        """

        return self._connection_storage

    @connection_storage.setter
    def connection_storage(self, connection_storage:ConnectionStorage):
        """ Setter for the attribute : self.connection_storage

        Arguments:
            connection_storage {ConnectionStorage} -- New ConnectionStorage object.
        """

        self._connection_storage = connection_storage

    def __init__(self, credentials:Credentials):
        self.logger = logging.getLogger(self.__module__)
        self.basic = Basic(credentials=credentials)
        self.connection_storage = ConnectionStorage(basic=self.basic)

    def get_update(
            self,
            request_list:Update.RequestList,
            raw:bool=False,
        ):
        basic = self.basic
        session_id = self.connection_storage.session_id

        return basic.get_update(
            request_list=request_list,
            session_id=session_id,
            raw=raw,
        )

    def check_order(
            self, 
            order:Order,
            raw:bool=False,
        )->Union[Order.ConfirmationResponse, bool]:
        basic = self.basic
        session_id = self.connection_storage.session_id

        return basic.check_order(
            order=order,
            session_id=session_id,
            raw=raw,
        )

    def confirm_order(
            self,
            confirmation_id:str,
            order:Order,
            raw:bool=False,
        )->Union[Order.ConfirmationResponse, bool]:
        basic = self.basic
        session_id = self.connection_storage.session_id

        return basic.confirm_order(
            confirmation_id=confirmation_id,
            order=order,
            session_id=session_id,
            raw=raw,
        )
    
    def update_order(
            self, 
            order:Order,
            raw:bool=False,
        ):
        basic = self.basic
        session_id = self.connection_storage.session_id

        return basic.update_order(
            order=order,
            session_id=session_id,
            raw=raw,
        )

    def delete_order(
            self,
            order_id:str
        ) -> bool:
        basic = self.basic
        session_id = self.connection_storage.session_id

        return basic.delete_order(
            order_id=order_id,
            session_id=session_id
        )

if __name__ == "__main__":

    from trading.pb.trading_pb2 import (
        Action,
        Order,
        OrderType,
        TimeType,
        UpdateOption,
    )
    with open('config.json') as config_file:
        config = json.load(config_file)

    int_account = config['int_account']
    username = config['username']
    password = config['password']
    credentials = Credentials(
        int_account=int_account,
        username=username,
        password=password
    )
    api = API(credentials=credentials)

    # INITIALIZATION

    api.connection_storage.connect()
    
    order = Order(
        action=Action.Value('BUY'),
        order_type=OrderType.Value('LIMIT'),
        price=10.60,
        product_id=71981,
        size=1,
        time_type=TimeType.Value('GOOD_TILL_DAY')
    )
    print(order)
    # confirmation_id = api.check_order(order=order)
    # order = api.confirm_order(
    #     confirmation_id=confirmation_id,
    #     order=order
    # )

    option_list = UpdateOptionList(
        list=[
            UpdateOption.Value('ORDERS')
        ]
    )
    update = api.get_update(option_list=option_list)

    # print('session_id', api.connection_storage.session_id)
    # print('confirmation_id', confirmation_id)
    print('order', order)
    print(update)