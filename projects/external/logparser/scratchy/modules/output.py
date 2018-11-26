
import string
import sys
from types import *


def output(data, fd=sys.stdout, label=""):
    if label:
        fd.write("%s\n" % label)
    Output(data, fd)
    fd.write("\n")

    

class Output:
    def __init__(self, data, fd):
        self.fd = fd
        self.data = data
        self.indent = 0
        
        if type(data) == DictType:
            self.out_dict(data, self.indent)
        elif type(data) in (ListType, TupleType):
            self.out_list(data, self.indent)
        else:
            self.out_item(data, self.indent)

        
    def out_dict(self, dict_data, indent, from_dict=0):
        keys = dict_data.keys()
        keys.sort()
        if from_dict:
            self.fd.write(" [dict]\n")
        else:
            self.fd.write("%s%s\n" % ("\t" * indent, "[dict]"))
        
        tab = indent + 1
        for key in keys:
            item = dict_data[key]

            if type(item) == DictType:
                self.fd.write("%s%s:" % ("\t" * tab, key))
                self.out_dict(item, tab, 1)
            elif type(item) in (ListType, TupleType):
                self.fd.write("%s%s: " % ("\t" * tab, key))
                self.out_list(item, tab, 1)
            else:
                self.fd.write("%s%s: %s\n" % ("\t" * tab, key, item))

                
    def out_list(self, list_data, indent, from_dict=0):
        if type(list_data) == ListType:
            typestr = '[list]'
        else:
            typestr = '[tuple]'
            
        if not from_dict:
            self.fd.write("%s%s\n" % ("\t" * indent, typestr))
        else:
            self.fd.write("%s\n" % typestr)
            
        tab = indent + 1
        for item in list_data:
            if type(item) == DictType:
                self.out_dict(item, tab)
            elif type(item) in (ListType, TupleType):
                self.fd.write("%s%s:\n" % ("\t" * tab, item))
                self.out_list(item, tab + 1)
            else:
                self.out_item(item, tab)


    def out_item(self, item, indent):
        self.fd.write("%s%s\n" % ("\t" * indent, item))


def test():
    items = []
    dict1 = {'a': 123, 'b': 987}
    dict2 = {'test': 'aaaaaaa', 'name': 'value', 'items': [1,2,3,4], "nested dict 1" : dict1}
    items.append("string")
    items.append(dict1)
    items.append(dict1)
    items.append("float")
    items.append(dict2)
    items.append("integer")
    items.append("long")

    output(dict1, label="dict 1")
    output(dict2, label="dict 2")

    output(items, label="misc items")



    args = {'shipment': {'part_shipment_list': [{'tracked_part_id': 1, 'receipt_quantity': None, 'kanban_list': [{'quantity': 2500, 'packing_slip': 'Test', 'kanban_ssi_id': 1, 'hold': 0, 'customer_kanban_id': '1', 'type': 'Something 1', 'status': 'in-transit'}, {'quantity': 2500, 'packing_slip': 'Test', 'kanban_ssi_id': 2, 'hold': 0, 'customer_kanban_id': '1', 'type': 'Something 2', 'status': 'in-transit'}], 'receipt_timestamp': None, 'shipping_quantity': 5000, 'received_by_user_id': None, 'part_shipment_id': 1}, {'shipment_state': 'delete promise', 'tracked_part_id': 2, 'shipping_quantity': 100, 'part_shipment_id': 2}, {'tracked_part_id': 3, 'shipping_quantity': 111111, 'part_shipment_id': 3}], 'common_data': {'source_user_id': 1, 'shipment_set_id': 19L}}}

    output(args, label="shipping args")

    result ={'timestamp': '1019517961300', 'updates': [{'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019234475908', 'receipt_timestamp': '1019234475909', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019234483404', 'transit_code': 'XX', 'eta': '1019234475908', 'shipped_by_username': None, 'shipment_set_id': '8', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '7'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019234896173', 'receipt_timestamp': '1019234896174', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019234902548', 'transit_code': 'XX', 'eta': '1019234896173', 'shipped_by_username': None, 'shipment_set_id': '9', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '10'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019236209895', 'receipt_timestamp': '1019236209896', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019236216701', 'transit_code': 'XX', 'eta': '1019236209895', 'shipped_by_username': None, 'shipment_set_id': '11', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '13'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019236245919', 'receipt_timestamp': '1019236245920', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019236252322', 'transit_code': 'XX', 'eta': '1019236245919', 'shipped_by_username': None, 'shipment_set_id': '12', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '16'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019236551835', 'receipt_timestamp': '1019236551837', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019236559335', 'transit_code': 'XX', 'eta': '1019236551835', 'shipped_by_username': None, 'shipment_set_id': '13', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '19'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019239870091', 'receipt_timestamp': '1019239870092', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019239877738', 'transit_code': 'XX', 'eta': '1019239870091', 'shipped_by_username': None, 'shipment_set_id': '14', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '22'}, {'packing_slip': 'Test', 'tracked_part_id': '1', 'receipt_quantity': None, 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019240222443', 'receipt_timestamp': None, 'shipping_quantity': '50', 'shipment_state': 'promise', 'erp_shipment_override': '0', 'timestamp': '1019240224692', 'transit_code': None, 'eta': '1019240222443', 'shipped_by_username': None, 'shipment_set_id': '15', 'received_by_user_id': None, 'trading_pair_id': '1', 'part_shipment_id': '25'}, {'packing_slip': 'Test', 'tracked_part_id': '1', 'receipt_quantity': None, 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019240336039', 'receipt_timestamp': None, 'shipping_quantity': '50', 'shipment_state': 'promise', 'erp_shipment_override': '0', 'timestamp': '1019240338042', 'transit_code': None, 'eta': '1019240336039', 'shipped_by_username': None, 'shipment_set_id': '16', 'received_by_user_id': None, 'trading_pair_id': '1', 'part_shipment_id': '28'}, {'packing_slip': 'test asn', 'tracked_part_id': '1', 'receipt_quantity': '1001', 'duration': '36', 'shipped_by_user_id': '2', 'shipping_timestamp': '1003284120000', 'receipt_timestamp': '1019490219496', 'shipping_quantity': '1001', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019490220614', 'transit_code': 'RR', 'eta': '100328412000036', 'shipped_by_username': None, 'shipment_set_id': '1000', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '43'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019507806086', 'receipt_timestamp': '1019507806088', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019507815255', 'transit_code': 'XX', 'eta': '1019507806086', 'shipped_by_username': None, 'shipment_set_id': '17', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '38'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '1', 'receipt_quantity': '50', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019517670898', 'receipt_timestamp': '1019517670900', 'shipping_quantity': '50', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019517682544', 'transit_code': 'XX', 'eta': '1019517670898', 'shipped_by_username': None, 'shipment_set_id': '18', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '45'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019234475908', 'receipt_timestamp': '1019234475909', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019234483404', 'transit_code': 'XX', 'eta': '1019234475908', 'shipped_by_username': None, 'shipment_set_id': '8', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '8'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019234896173', 'receipt_timestamp': '1019234896174', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019234902548', 'transit_code': 'XX', 'eta': '1019234896173', 'shipped_by_username': None, 'shipment_set_id': '9', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '11'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019236209895', 'receipt_timestamp': '1019236209896', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019236216701', 'transit_code': 'XX', 'eta': '1019236209895', 'shipped_by_username': None, 'shipment_set_id': '11', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '14'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019236245919', 'receipt_timestamp': '1019236245920', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019236252322', 'transit_code': 'XX', 'eta': '1019236245919', 'shipped_by_username': None, 'shipment_set_id': '12', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '17'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019236551835', 'receipt_timestamp': '1019236551837', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019236559335', 'transit_code': 'XX', 'eta': '1019236551835', 'shipped_by_username': None, 'shipment_set_id': '13', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '20'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019239870091', 'receipt_timestamp': '1019239870092', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019239877738', 'transit_code': 'XX', 'eta': '1019239870091', 'shipped_by_username': None, 'shipment_set_id': '14', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '23'}, {'packing_slip': 'Test', 'tracked_part_id': '2', 'receipt_quantity': None, 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019240222443', 'receipt_timestamp': None, 'shipping_quantity': '100', 'shipment_state': 'promise', 'erp_shipment_override': '0', 'timestamp': '1019240224692', 'transit_code': None, 'eta': '1019240222443', 'shipped_by_username': None, 'shipment_set_id': '15', 'received_by_user_id': None, 'trading_pair_id': '1', 'part_shipment_id': '26'}, {'packing_slip': 'Test', 'tracked_part_id': '2', 'receipt_quantity': None, 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019240336039', 'receipt_timestamp': None, 'shipping_quantity': '100', 'shipment_state': 'promise', 'erp_shipment_override': '0', 'timestamp': '1019240338042', 'transit_code': None, 'eta': '1019240336039', 'shipped_by_username': None, 'shipment_set_id': '16', 'received_by_user_id': None, 'trading_pair_id': '1', 'part_shipment_id': '29'}, {'packing_slip': 'test asn', 'tracked_part_id': '2', 'receipt_quantity': '2000', 'duration': '36', 'shipped_by_user_id': '2', 'shipping_timestamp': '1003284120000', 'receipt_timestamp': '1019490219496', 'shipping_quantity': '2000', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019490220614', 'transit_code': 'RR', 'eta': '100328412000036', 'shipped_by_username': None, 'shipment_set_id': '1000', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '44'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019507806086', 'receipt_timestamp': '1019507806088', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019507815255', 'transit_code': 'XX', 'eta': '1019507806086', 'shipped_by_username': None, 'shipment_set_id': '17', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '39'}, {'packing_slip': 'Test - modified', 'tracked_part_id': '2', 'receipt_quantity': '100', 'duration': None, 'shipped_by_user_id': '1', 'shipping_timestamp': '1019517670898', 'receipt_timestamp': '1019517670900', 'shipping_quantity': '100', 'shipment_state': 'receipt', 'erp_shipment_override': '0', 'timestamp': '1019517682544', 'transit_code': 'XX', 'eta': '1019517670898', 'shipped_by_username': None, 'shipment_set_id': '18', 'received_by_user_id': '2', 'trading_pair_id': '1', 'part_shipment_id': '46'}]}

    output(result, label="shipping result")
    

if __name__ == '__main__':
    test()




