class Models:
    def __init__(self, table):
        self.table = table

    def get_one(self, data_dict):
        return self.table.find_one(data_dict)

    def get_all(self, options=None):
        if options is None:
            return self.table.find()
        else:
            return self.table.find(options)

    def get_all_exclude(self, exclude):
        return self.table.find(exclude)

    def get_many(self, data):
        return self.table.find(data)

    def create(self, data_dict):
        return self.table.insert_one(data_dict)

    def update(self, _id, data_dict):
        return self.table.find_one_and_update({
            '_id': _id
            }, {
                '$set': data_dict
            }
        )

    def delete_one(self, _id):
        self.table.find_one_and_delete({'_id': _id})

    def delete_many(self, data_dict):
        pass
