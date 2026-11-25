from collections import Counter
from itertools import count

from MNeuEventGUI.presenter_template import PresenterTemplate
from MNeuEventGUI.table.view import TableView
from MNeuEventGUI.utils.batch import batch_label
from MNeuEventGUI.utils.errors import GUIError


class TablePresenter(PresenterTemplate):
    """
    A class for the view of the filter
    table. This follows the MVP
    pattern.
    """
    # the key for the table's filters in the data's dict
    FILTER_KEY = None

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
        self.count = count(start=1)

        self.cols = columns
        self._view = self._set_view()

    def _set_view(self):
        """
        A method to set the view for the widget
        :returns: the view for the widget
        """
        return TableView(self)

    def batch_filters(self, batch):
        """
        Gets a batch's filters from the data.
        :param batch: the index of the batch
        :returns: the filters (a dict keyed by name)
        """
        return self.data._dict(batch)[self.FILTER_KEY]

    def new_filter_name(self, batch):
        """
        Gets a name for a new filter, which does not
        overwrite any of the batch's existing filters.
        :param batch: the index of the batch
        :returns: the name
        """
        existing_filters = self.batch_filters(batch)
        name = f"filter {next(self.count)}"
        while name in existing_filters:
            name = f"filter {next(self.count)}"
        return name

    def add(self, batch) -> dict:
        """
        Adds a row to the table.
        :param batch: the index of the active batch
        :returns: the new data for the table.
        """
        raise NotImplementedError

    def reject(self, data, msg, batch):
        """
        Rejects an edit to the table. The corrected data is
        carried on the error, because a callback that raises
        does not update its own outputs.
        :param data: the corrected table data (list of rows)
        :param msg: why the edit was rejected
        :param batch: the index of the active batch, so the
        user knows which batch the error came from
        :raises GUIError: always
        """
        raise GUIError(f'{batch_label(batch)}: {msg}',
                       {self.ID: {'rowData': data}})

    def validate(self, row, data, batch):
        """
        A validation check for the table.
        It has a rule that each row name
        must be unique.
        :param row: the change in the table (row)
        :param data: the data in the table (list of rows)
        :param batch: the index of the active batch
        :returns: the data to update the table with
        :raises GUIError: if the new name is already in use
        """
        names = [row['Name_' + self.ID] for row in data]
        repeat, num = Counter(names).most_common(1)[0]
        if num > 1:
            data[row[0]['rowIndex']]['Name_'+self.ID] = row[0]['oldValue']
            self.reject(data, f'Repeated name {repeat}', batch)

        return self.validate_row(row, data, batch)

    def validate_row(self, change, data, batch):
        """
        A validation check for the table.
        It has a rule that each row name
        must be unique.
        :param change: the change in the table (row)
        :param data: the data in the table (list of rows)
        :param batch: the index of the active batch
        :returns: the data to update the table with
        """
        changed = change[0]
        col_name = changed['colId']
        row = changed['data']

        data[changed['rowIndex']][col_name] = row[col_name]
        return data

    def delete_row(self, info: dict, data: dict, batch) -> dict:
        """
        Remove a row from a table.
        :param info: dict of information about deleted row
        :param data: the table data (list of rows)
        :param batch: the index of the active batch
        :returns: Updated data values
        """
        raise NotImplementedError

    def edit_row(self, info: dict, data: dict, batch) -> dict:
        """
        Edit a row in the table.
        :param info: dict of information about deleted row
        :param data: the table data (list of rows)
        :param batch: the index of the active batch
        :returns: Updated table values
        """
        raise NotImplementedError

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
