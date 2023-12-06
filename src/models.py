class Models:
    def __init__(self, table):
        self.table = table

    def get_one(self, data_dict):
        data = self.table.find_one(data_dict)
        return data

    def get_many(self):
        data_list = self.table.find()
        return data_list

    def create(self, data_dict):
        data = self.table.insert_one(data_dict)
        return data

    def update(self, _id, data_dict):
        data = self.table.find_one_and_update({
            '_id': _id
            }, {
                '$set': data_dict
            }
        )
        return data

    def delete(self):
        pass
