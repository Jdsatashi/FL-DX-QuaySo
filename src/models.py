import math


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

    def get_many(self, data):
        return self.table.find(data)

    def create(self, data_dict):
        return self.table.insert_one(data_dict)

    def create_many(self, data_list):
        return self.table.insert_many(data_list)

    def update(self, _id, data_dict):
        return self.table.find_one_and_update({
            '_id': _id
        }, {
            '$set': data_dict
        })

    def delete_one(self, _id):
        self.table.find_one_and_delete({'_id': _id})

    def delete_many(self, data_dict):
        pass

    def pagination(self, current_page: int, perpage: int, query_data: dict, sorting: list = None):
        table = self.table
        if sorting is None:
            sorting = []
        if current_page <= 0:
            current_page = 1
        # Get total items in table
        total_data = table.count_documents(query_data)
        # From total items then calculate maximum page size | math.ceil make 4.8 to 5
        total_pages = math.ceil(total_data / perpage)
        # If current page is over max page then reset to max page
        if current_page > total_pages:
            current_page = total_pages
        # Skip data
        skip_data = (current_page - 1) * perpage
        if skip_data < 0:
            skip_data = 0
        # Optional sorting or not
        if sorting is not None and len(sorting) > 0:
            data_list = list(table.find(query_data).sort(sorting).limit(perpage).skip(skip_data))
        else:
            data_list = list(table.find(query_data).limit(perpage).skip(skip_data))

        return data_list, total_pages
