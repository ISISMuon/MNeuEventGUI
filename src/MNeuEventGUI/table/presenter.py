from MuonDataLib.GUI.presenter_template import PresenterTemplate
from MuonDataLib.GUI.table.view import TableView

from collections import Counter


class TablePresenter(PresenterTemplate):
    """
    A class for the view of the filter
    table. This follows the MVP
    pattern.
    """
    def __init__(self, ID, columns, name_col):
        """
        This creates the view object for the
        widget. The responses to the callbacks
        will be in the presenter.
        :param ID: the ID for the table
        :param columns: a list of the columns for the
        table (see column.py)
        :param name_col: the string used to identify the name
        column for the specific table
        """
        self.ID = ID
        self.name_col = name_col
        self.count = 0

        self.cols = columns
        self._view = self._set_view()

    def _set_view(self):
        """
        A method to set the view for the widget
        :returns: the view for the widget
        """
        return TableView(self)

    def add(self, n, data):
        """
        Adds a row to the table.
        :param n: the number of clicks of the add button
        :param data: A list of the row data (as a dict)
        :returns: the data for the table and if its valid
        """
        if not isinstance(data, list):
            data = []
        data.append(self.generate_default)
        return data

    def validate(self, row, data):
        """
        A validation check for the table.
        It has a rule that each row name
        must be unique.
        :param row: the change in the table (row)
        :param data: the data in the table (list of rows)
        :returns it to update and the error message
        """
        names = [row['Name_' + self.ID] for row in data]
        repeat, num = Counter(names).most_common(1)[0]
        if num > 1:
            data[row[0]['rowIndex']]['Name_'+self.ID] = row[0]['oldValue']
            return data, f'Repeated name {repeat}'

        return self.validate_row(row, data)

    def validate_row(self, change, data):
        """
        A validation check for the table.
        It has a rule that each row name
        must be unique.
        :param change: the change in the table (row)
        :param data: the data in the table (list of rows)
        :returns: it to update and the error message
        """
        changed = change[0]
        col_name = changed['colId']
        row = changed['data']

        data[changed['rowIndex']][col_name] = row[col_name]
        return data, ''

    def delete_row(self, info, data):
        """
        A method to remove a row from a table.
        :param info: dict of intormation about deleted row
        :param data: the table data (list of rows)
        :returns: Updated data values
        """
        data.pop(info['rowIndex'])
        return data

    @property
    def get_next_row_name(self):
        """
        Gets a name for a new row.
        This provides the name
        default_N, where N is the number
        of times this method has been called
        :returns: the name
        """
        self.count += 1
        return f'default_{self.count}'

    @property
    def generate_default(self):
        """
        Code to create some default values
        :returns: a default dict
        """
        return {'Delete_' + self.ID: '',
                self.name_col: self.get_next_row_name,
                **self.default_row}

    @property
    def default_row(self):
        """
        This will define the default row for the table
        """
        raise NotImplementedError(f"Need to set a default_row for {self.ID}")

    @property
    def _delete_row_col(self):
        """
        This gets the dict for defining a
        delete button
        :returns: the dict of delete button
        """
        return {'field': 'Delete_t',
                'headerName': '',
                'width': 100,
                'editable': False,
                'cellRenderer': 'Button',
                'cellRendererParams': {'Icon': 'bi bi-trash me-2',
                                       'className': 'btn btn-danger'}
                }
