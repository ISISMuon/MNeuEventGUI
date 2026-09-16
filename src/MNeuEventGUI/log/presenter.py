import numpy as np
from MuonDataLib.data.utils import NONE
from MuonDataLib.filters import Filter

from MNeuEventGUI.log.view import LogView
from MNeuEventGUI.plot_area.presenter import PlotAreaPresenter
from MNeuEventGUI.table.column import (
    ButtonColumn,
    DropDownColumn,
    NumericColumn,
    TableColumns,
    TableGroup,
    TextColumn,
)
from MNeuEventGUI.table.presenter import TablePresenter

LOG_TABLE = 'log-table'


class LogPresenter(TablePresenter):
    """
    A class for the view of the sample log filter
    widget. This follows the MVP
    pattern.
    """
    def __init__(self):
        """
        This creates the presenter object for the
        widget.
        """

        # a handle to the data object
        self._data = None
        # a list of default sample logs
        self._defaults = ['Temp_Sample']
        # number of time ok has been clicked in pop-up
        self._ok_clicks = 0
        # if we are replacing a sample log (if so which row)
        self._replace = None
        # the current name for the pop up
        self._selected_name = self._defaults[0]
        # create a plot area for pop up
        self._plot = PlotAreaPresenter('log')

        # create table
        name = TextColumn('Name_' + LOG_TABLE, 'Name')

        log = ButtonColumn('change_btn_' + LOG_TABLE, '')
        log.set_icon(icon='bi bi-graph-up me-2', class_name='btn btn-primary')

        sample = TextColumn('sample_' + LOG_TABLE, 'selected')
        sample.set_uneditable()

        filter_selector = DropDownColumn('filter_' + LOG_TABLE, 'Filter type')
        """
        we need an extra magic col as we cannot get the value from the
        dropdown in conditional formatting
        """
        magic = TextColumn('magic', '')
        magic.hide()

        filter_start = NumericColumn('y0_' + LOG_TABLE, 'Keep data from')
        filter_end = NumericColumn('yN_' + LOG_TABLE, 'Keep data to')

        filter_start.set_condition({"styleConditions": [
            {"condition": "params.data.magic == 'below'",
             "style": {"backgroundColor": "black"}},
            ],
            "defaultStyle": {"backgroundColor": "white"}
                 })

        filter_end.set_condition({"styleConditions": [
            {"condition": "params.data.magic == 'above'",
             "style": {"backgroundColor": "black"}},
            ],
            "defaultStyle": {"backgroundColor": "white"}
                 })

        # want the min and max y values in the row data to make it easier.
        y_min = NumericColumn('y_min_' + LOG_TABLE, 'y min')
        y_min.hide()
        y_max = NumericColumn('y_max_' + LOG_TABLE, 'y max')
        y_max.hide()
        cols = TableColumns([TableGroup([name]),
                             TableGroup([log, sample], 'Sample logs'),
                             TableGroup([filter_selector,
                                         filter_start,
                                         filter_end,
                                         magic,
                                         y_min,
                                         y_max],
                                        'Filter Details')],
                            inc_delete_row=True,
                            btn_ID=LOG_TABLE)

        super().__init__(LOG_TABLE,
                         cols,
                         name.ID)

    def _set_view(self):
        """
        Overwrite the view to give a time table view
        :returns: the log table view
        """
        return LogView(self)

    def set_data(self, data):
        """
        Set the data object.
        :param logs: the data object
        """
        self._data = data

    def validate_row(self, change, data):
        """
        This checks if the new row values are valid.
        It will also keep the 'magic' column in sync
        with the dropdown selection.
        :param change: a dict of information on the
        changed row
        :param data: the data from the sample log
        filter table.
        :returns: the updated sample log table and
        an error message
        """
        changed = change[0]
        col_name = changed['colId']
        row = changed['data']

        msg = ''
        new_value = row[col_name]

        f_type = row['magic']
        y_min = row['y_min_' + LOG_TABLE]
        y_max = row['y_max_' + LOG_TABLE]

        if col_name == 'y0_' + LOG_TABLE:
            if new_value < y_min:
                # check its within data range, above min
                msg = (f'The new filter value {new_value} '
                       f'is below the lowest y value '
                       f'{row["y_min_" + LOG_TABLE]} for the data.')
                new_value = changed['oldValue']
            elif new_value > y_max:
                # check its within data range, above max
                msg = (f'The new filter value {new_value} '
                       f'is above the max y value '
                       f'{y_max}')
                new_value = changed['oldValue']

            elif f_type == 'above':
                # check if need to update yN
                if new_value < y_max and new_value > row['yN_' + LOG_TABLE]:
                    # only update if it would cause start > end
                    data[changed['rowIndex']]['yN_' + LOG_TABLE] = y_max

            elif new_value > row['yN_' + LOG_TABLE] and f_type == 'between':
                # check its below the max filter value if between
                msg = (f'The new filter value {new_value} '
                       f'is above the upper filter value '
                       f'{row["yN_" + LOG_TABLE]}.')
                new_value = changed['oldValue']

            elif f_type == 'below' and new_value != y_min:
                # silently fix the value if not used
                new_value = changed['oldValue']

        elif col_name == 'yN_' + LOG_TABLE:
            if new_value > y_max:
                # check its within data range
                msg = (f'The new filter value {new_value} '
                       f'is above the largest y value '
                       f'{row["y_max_" + LOG_TABLE]} for the data.')
                new_value = changed['oldValue']

            elif f_type == 'below':
                if new_value > y_min and new_value < row['y0_' + LOG_TABLE]:
                    data[changed['rowIndex']]['y0_' + LOG_TABLE] = y_min
                elif new_value < y_min:
                    msg = (f'The new filter value {new_value} '
                           f'is below the minimum value '
                           f'{y_min}.')
                    new_value = changed['oldValue']

            elif new_value < row['y0_' + LOG_TABLE] and f_type == 'between':
                # check its above min filter value
                msg = (f'The new filter value {new_value} '
                       f'is below the lower filter value '
                       f'{row["y0_" + LOG_TABLE]}.')
                new_value = changed['oldValue']

            elif f_type == 'above' and new_value != y_max:
                new_value = changed['oldValue']

        elif col_name == 'filter_' + LOG_TABLE:
            # update the filter type (for conditional formatting)
            new_value = change[0]['data']['filter_' + LOG_TABLE]
            col_name = 'magic'

        data[changed['rowIndex']][col_name] = new_value

        return data, msg

    def btn_pressed(self, info, data):
        """
        It is not possible to differentiate between
        different buttons in the same table. So
        we use this method to identify which one was pressed
        and to do the correct response. The options are:
        - Open sample log pop up
        - delete row
        :param info: the information on the button pressed
        :param data: the data from the table
        :returns: the updated data and if to open the sample log pop up
        """
        if 'change_btn_log-table' == info['colId']:
            self._selected_name = data[info['rowIndex']]['sample_log-table']
            self._replace = info['rowIndex']
            return data, True
        else:
            return self.delete_row(info, data), False

    def get_new_log_name(self, data):
        """
        This gets the name of the next sample log,
        based on the default list and then just the
        first one that is not in use.
        :param data: the sample log table data
        :returns: the next name to be used
        """
        if self._data is None:
            return ''
        names = self._data.dataset.get_log_names()
        for default in self._defaults:
            if default in names:
                return default
        return names[0]

    def show_log_data(self, name):
        """
        This method is to populate the sample log pop up with
        stats and a nice plot.
        :param name: name of the sample log to be displayed
        :returns: for the sample log (name) it will yield:
        - a plot of the data
        - the max y value
        - the mean y value
        - the min y value
        - the sigma (std)
        """
        log = self._data.dataset.get_sample_log(name)
        value = log['value']

        return (self._plot.new_plot([name], log),
                f'Max: {np.max(value):.3f}',
                f'Mean: {np.mean(value):.3f}',
                f'Min: {np.min(value):.3f}',
                f'Sigma (std): {np.std(value):.3f}')

    def select_log(self, is_open, data):
        """
        This method sets up the combo box for
        the pop up.
        :param is_open: if the pop up is open (not used)
        :param data: the sample log table data
        :returns: a list of names for the combo box and the
        selected value
        """
        options = self._data.dataset.get_log_names()
        # if replacing/updating a row want to keep the name
        if self._replace is not None:
            return options, self._selected_name
        return options, self.get_new_log_name(data)

    def close_modal(self, ok, cancel, name, data):
        """
        A method for closing the pop up. To tell
        if ok or cancel has been pressed we track
        the number of ok presses. If ok is pressed
        we update the sample log table. If cancel is
        pressed we don't change the sample log table.
        :param ok: number of times ok has been pressed
        :param cancel: the number of times cancel has
        been pressed
        :param name: the name of the sample log being viewed
        (if ok is pressed it will be added/updated in the table)
        :param data: the sample log table data
        :returns if the pop up is open (always no) and
        the updated sample log table data.
        """
        del self._plot.fig
        self._plot.fig = None

        # was ok or cancel pressed?
        if self._ok_clicks < ok:
            # ok pressed
            row = 0
            if self._replace is not None:
                # replace/update row (i.e. graph button pressed)
                data[self._replace]['sample_log-table'] = name
                row = self._replace
            else:
                # new row (i.e. from add button)
                data.append(self.generate_default(data,
                                                  name))
                row = len(data) - 1
            self._ok_clicks += 1
            log = self._data.get_sample_log(name)

            min_value = np.min(log['value'])
            data[row]['y_min_' + LOG_TABLE] = min_value
            data[row]['y0_' + LOG_TABLE] = min_value

            max_value = np.max(log['value'])
            data[row]['y_max_' + LOG_TABLE] = max_value
            data[row]['yN_' + LOG_TABLE] = max_value
        return False, data

    def add(self, n, data):
        """
        Adds a row to the table.
        :param n: the number of clicks of the add button
        :param data: A list of the row data (as a dict)
        :returns: if the pop up should be opened (always yes)
        and the name of the selected sample log on opening
        """
        self._replace = None
        self._selected_name = self.get_new_log_name(data)
        return True, self.get_new_log_name(data)

    def generate_default(self, data, name):
        """
        Code to create some default values
        :returns: a default dict
        """
        default_filter = 'between'
        return {'Delete_' + self.ID: '',
                self.name_col: 'log_' + self.get_next_row_name,
                'sample_log-table': name,
                'filter_' + LOG_TABLE: default_filter,
                'y0_' + LOG_TABLE: 0,
                'yN_' + LOG_TABLE: 1,
                'magic': default_filter,
                'y_min_' + LOG_TABLE: 0,
                'y_max_' + LOG_TABLE: 1}

    def load(self, filters: list[Filter]):
        """
        A method to load filters from a json file
        If the filter values are outside of the data
        range, they will be updated to be within the
        range of possible y values.
        :param filters: the list of filters.
        :returns: a list of the row details
        for the log table (exluding the remove button),
        """
        data = []
        for f in filters:
            key = f.name
            start = f.start
            end = f.end

            log = self._data.get_sample_log(key)
            y = log['value']

            y_min = np.min(y)
            y_max = np.max(y)
            y_0 = y_min
            y_N = y_max
            if start == NONE:
                load_filter = 'below'
                if y_min < end < y_max:
                    y_N = end

            elif end == NONE:
                load_filter = 'above'
                if start > y_min:
                    y_0 = start

            else:
                load_filter = 'between'
                y_0 = start
                y_N = end
            data.append({self.name_col: 'log_' + self.get_next_row_name,
                         'sample_log-table': key,
                         'filter_' + LOG_TABLE: load_filter,
                         'y0_' + LOG_TABLE: y_0,
                         'yN_' + LOG_TABLE: y_N,
                         'magic': load_filter,
                         'y_min_' + LOG_TABLE: y_min,
                         'y_max_' + LOG_TABLE: y_max})

        return data
