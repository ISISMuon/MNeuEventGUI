from abc import ABC, abstractmethod


class Column(ABC):
    """
    A simple class for creating columns for
    a dash data ag-table. This stores the extra
    information (e.g. dropdowns, validation,
    conditional formating).
    """
    def __init__(self, ID, name):
        """
        Create the details for the column.
        :param ID: the ID for the column
        :param name: the displayed name in the
        column.
        """
        self.ID = ID
        self.name = name
        self._editable = True
        self._con = None
        self._hide = False

    def set_uneditable(self):
        """
        A method to make the column uneditable
        """
        self._editable = False

    def set_condition(self, condition):
        """
        This sets conditions for the cells.
        e.g.

        {"styleConditions": [
            {"condition": "params.data.magic == 'below'",
             "style": {"backgroundColor": "black"}},
            ],
            "defaultStyle": {"backgroundColor": "white"}
        }

        :param condition: the condition to add to the cell.
        Set to None to remove a condition.
        """
        self._con = condition

    def hide(self):
        """
        hides the column
        """
        self._hide = True

    @property
    def get_column_dict(self):
        """
        Thos method generates a dict
        for the config of the column.
        :returns: the dict of the config
        """
        col = {'field': self.ID,
               'headerName': self.name,
               'width': 100,
               'editable': self._editable,
               'hide': self._hide}
        col.update(self.get_cell_config())

        if self._con is not None:
            col['cellStyle'] = self._con
        return col

    @abstractmethod
    def get_cell_config(self):
        """
        Get dash cell configuration details
        for a specific data type.
        :returns: the config for the specific cell type
        """
        raise NotImplementedError


class TextColumn(Column):
    """
    A column subclass for storing text data.
    """
    def get_cell_config(self):
        return {
            'cellEditor': 'agLargeTextCellEditor',
            'cellEditorPopup': False,
            'cellEditorParams': {'maxLength': 50},
            }


class NumericColumn(Column):
    """
    A column subclass for storing numeric data.
    """
    def __init__(self, ID, name):
        super().__init__(ID, name)
        self._min = -1e6
        self._max = 1e6

    def get_cell_config(self):
        return {
            'cellEditor': 'agNumberCellEditor',
            'cellEditorParams': {'min': self._min,
                                 'max': self._max,
                                 'precision': 5}
            }

    def set_range(self, min_value, max_value):
        """
        Sets the range of allowed values for a numeric
        cell.
        :param min_value: the smallest allowed value
        :param max_value: the largest allowed value
        """
        if min_value > max_value:
            raise ValueError("col range: Min value > Max value")
        self._min = min_value
        self._max = max_value


class ButtonColumn(Column):
    """
    A column subclass for storing buttons.
    """
    def __init__(self, ID, name):
        super().__init__(ID, name)
        # set default button values (delete)
        self._icon = 'bi bi-trash me-2'
        self._className = 'btn btn-danger'

    def get_cell_config(self):
        return {
            'editable': False,
            'cellRenderer': 'Button',
            'cellRendererParams': {'Icon': self._icon,
                                   'className': self._className}

            }

    def set_icon(self, icon, class_name):
        """
        A method to set the column's button to a
        custom one.
        :param icon: the code for the button image
        see https://icons.getbootstrap.com/
        :param class_name: the class name
        for the button (sets colour)
        """
        self._icon = icon
        self._className = class_name


class DropDownColumn(Column):
    """
    A simple class for creating dropdown
    columns for a dash data ag-table.
    """
    def get_cell_config(self):
        return {
           "cellEditor": "agSelectCellEditor",
           "cellEditorParams": {"values": ["above", "between", "below"]},
           'singleClickEdit': True,
            }


class TableGroup(object):
    def __init__(self, cols, name=None):
        """
        A class to store multiple related table
        columns. These may share a header
        (e.g. "Include data" for columns of the
        start and end values for the filters).
        :param cols: A list of columns (see above)
        :param name: The header name that is shared for
        all of the columns.
        """
        self.name = name
        if name is not None and len(cols) > 0:
            self._set_cols(cols)
        elif (len(cols) > 1 and name is None) or len(cols) == 0:
            raise ValueError("Must name the group of columns")
        else:
            self._set_cols(cols)

    def _set_cols(self, cols):
        if isinstance(cols, list):
            self.cols = []
            for c in cols:
                if isinstance(c, Column):
                    self.cols.append(c)
                else:
                    raise ValueError("Must use Columns")
        else:
            raise ValueError("Must use Columns")

    def set_range(self, min_value, max_value):
        """
        Sets the numeric ranges for all of the columns
        in the group. They will share values in time (x).
        :param min_value: the lowest allowed value
        :param max_value: the largst allowed value
        """
        for col in self.cols:
            if isinstance(col, NumericColumn):
                col.set_range(min_value,
                              max_value)

    @property
    def get_column_dict(self):
        """
        Creates a dict for the columns in the group.
        :returns: a dict of columns (json format)
        """
        if self.name is None:
            return [col.get_column_dict for col in self.cols]
        else:
            children = [col.get_column_dict for col in self.cols]
            return [{'headerName': self.name,
                     'children': children}]

    def set_title(self, title):
        """
        Sets the shared title for the group
        :param title: the new shared title
        """
        self.name = title


class TableColumns(object):
    def __init__(self, col_groups, inc_delete_row, btn_ID=''):
        """
        A class for holding column groups (above).
        This creates the nice table for the GUI,
        including a delete row button
        :param col_groups: a list of the column group objects
        :param inc_delete_row" if to add a delete button to the rows
        :param btn_ID: the ID for the row button
        """
        self.cols = []
        if len(col_groups) <= 0:
            raise ValueError("List of TableGroups must be at least 1")
        if inc_delete_row and btn_ID == '':
            raise RuntimeError('Need to include an ID '
                               'for the delete button')
        elif inc_delete_row:
            self.cols = [TableGroup([ButtonColumn('Delete_' + btn_ID, '')])]

        if isinstance(col_groups, list):
            for tmp in col_groups:
                if isinstance(tmp, TableGroup):
                    self.cols.append(tmp)
                else:
                    raise ValueError("Must use TableGroup's as input")

    def set_title(self, index, title):
        """
        Sets the shared title for a specific group
        :param index: the index for the new shared title
        :param title: the new shared title
        """
        if index > len(self.cols) - 1:
            raise RuntimeError("Cannot set title, column group doesn't exist")
        self.cols[index].set_title(title)

    @property
    def get_column_dict(self):
        """
        returns the json dict for the columns,
        which defines the table.
        :returns: the dict of the columns
        """
        result = []
        for col in self.cols:
            result.append(*col.get_column_dict)
        return result

    def set_range(self, min_value, max_value):
        """
        Loops over all columns in the table
        and sets the allowed data range to match the
        provided values
        :param min_value: the smallest allowed value
        :param max_value: the largest allowed value
        """
        for col in self.cols:
            col.set_range(min_value,
                          max_value)
