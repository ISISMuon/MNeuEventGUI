from dash import no_update

from MNeuEventGUI.table.column import (
    NumericColumn,
    TableColumns,
    TableGroup,
    TextColumn,
)
from MNeuEventGUI.table.presenter import TablePresenter
from MNeuEventGUI.time.view import TimeView

TIME_TABLE = 'time-table'


class TimePresenter(TablePresenter):
    """
    A class for the view of the time filter
    widget. This follows the MVP
    pattern.
    """
    FILTER_KEY = 'time_filters'

    def __init__(self):
        """
        This creates the presenter object for the
        widget.
        """
        self._previous = 'Include'
        self.data = None

        # create columns
        name = TextColumn('Name_' + TIME_TABLE, 'Name')

        start = NumericColumn('Start_' + TIME_TABLE, 'Start')
        end = NumericColumn('End_' + TIME_TABLE, 'End')

        cols = TableColumns([TableGroup([name]),
                             TableGroup([start,
                                         end],
                                        'Include Filter details')],
                            inc_delete_row=True,
                            btn_ID=TIME_TABLE)

        super().__init__(TIME_TABLE,
                         cols,
                         name.ID)
        self.start = 0
        self.end = 1000

    def _set_view(self):
        """
        Overwrite the view to give a time table view
        """
        return TimeView(self)

    def set_data(self, data):
        """
        Set the underlying model data.
        """
        self.data = data
        # set allowed time range for filters
        times = self.data.dataset.get_frame_times() * 1e-9
        frame_length = 32.e-6
        self.set_time_range(times[0], times[-1] + frame_length)

    def set_time_range(self, start, end):
        """
        Sets the range of allowed times
        :param start: the start time for the data
        :param end: the end time for the data
        """
        self.start = start
        self.end = end
        self.cols.set_range(start, end)

    def validate_row(self, change, data, batch):
        """
        A validation check for the table.
        It has a rule that each row name
        must be unique.
        :param change: the change in the table (row)
        :param data: the table data as a list of rows (dicts)
        :param batch: the index of the active batch
        :returns: the data to update the table with
        :raises GUIError: if the new value is not valid
        """
        changed = change[0]
        col_name = changed['colId']
        row = changed['data']

        msg = ''
        new_value = row[col_name]
        if new_value is None:
            # keep the old one
            msg = (f'The new value is '
                   f'outside of the data range.'
                   f' Range is {self.start} to {self.end}')
            new_value = changed['oldValue']
        elif col_name == 'Start_' + TIME_TABLE:
            end_value = row['End_' + TIME_TABLE]
            if new_value >= end_value:
                # keep the old one
                msg = (f'The start value {new_value} is '
                       f'larger than the end value {end_value}')
                new_value = changed['oldValue']
        elif col_name == 'End_' + TIME_TABLE:
            start_value = row['Start_' + TIME_TABLE]
            if new_value <= start_value:
                # keep the old one
                msg = (f'The end value {new_value} is '
                       f'smaller than the start value {start_value}')
                new_value = changed['oldValue']
        data[changed['rowIndex']][col_name] = new_value
        if msg:
            self.reject(data, msg, batch)
        return data

    @staticmethod
    def get_range(data):
        """
        Gets the x range from the time table data.
        Used for creating shaded region for the row
        :peram data' The row data from the table
        :returns: the start and end values
        """
        return [data['Start_' + TIME_TABLE], data['End_' + TIME_TABLE]]

    def show_state(self, value):
        """
        Sets the group name in the table, without
        changing the data.
        :param value: the updated part of the table name
        (expect either Include or Exclude)
        """
        self.cols.set_title(2, f'{value} Filter details')

    def set_state(self, value, batch):
        """
        Sets the group name in the table, and the
        filter type in the data.
        :param value: the updated part of the table name
        (expect either Include or Exclude)
        :param batch: the index of the active batch
        """
        self.show_state(value)
        if self.data is None:
            return
        self.data.set_time_type(batch, value)

    def update_state(self, value, changed, batch):
        """
        Updates the filter type and everything
        that depends on it. Nothing is updated if the
        batch already has this filter type, which is the
        case when the dropdown is filled from the data
        (e.g. when the active batch changes).
        :param value: the new filter type
        (expect either Include or Exclude)
        :param changed: the current value of the
        "state changed" signal
        :param batch: the index of the active batch
        :returns: the column headers and the new
        value for the "state changed" signal
        """
        if (self.data is not None
                and self.data._dict(batch)['time_filter_type'] == value):
            return no_update, no_update
        self.set_state(value, batch)
        # flipping the signal means it always reports a change
        return self.cols.get_column_dict, not changed

    def add(self, batch) -> dict:
        """
        Add a new time filter.
        :param batch: the index of the active batch
        :returns: The new time filter data.
        """
        # new row (i.e. from add button)
        self.data.add_time_filter(batch,
                                  self.new_filter_name(batch),
                                  0.33 * self.end,
                                  0.66 * self.end)
        return self.load(self.batch_filters(batch))

    def delete_row(self, info, data, batch):
        """
        Remove a row from a table.
        :param info: dict of intormation about deleted row
        :param data: the table data (list of rows)
        :param batch: the index of the active batch
        :returns: Updated data values
        """
        row = info["rowIndex"]
        name = data[row]['Name_' + TIME_TABLE]
        self.data.remove_time_filter(batch, name)
        return self.load(self.batch_filters(batch))

    def edit_row(self, info, data, batch):
        """
        Edit a row in the table.
        :param info: dict of information about deleted row
        :param data: the table data (list of rows)
        :param batch: the index of the active batch
        :returns: Updated table values
        """
        row = info[0]["rowIndex"]
        row_name = data[row]["Name_" + self.ID]

        # contrary to the Dash docs, the new value is "value" not "newValue"
        new_data = info[0]["data"]
        new_name = new_data["Name_" + self.ID]

        if new_name == row_name:
            self.data.edit_time_filter(batch, row_name,
                                       new_data["Start_" + self.ID],
                                       new_data["End_" + self.ID])
        else:
            # filters cannot be renamed, so replace it
            self.data.remove_time_filter(batch, row_name)
            self.data.add_time_filter(batch, new_name,
                                      new_data["Start_" + self.ID],
                                      new_data["End_" + self.ID])

        return self.load(self.batch_filters(batch))

    def load(self, filters: list[dict]):
        """
        A method to load filters from a list of filters.
        :param filters: the list of time filters.
        :returns: a list of the row details
        for the time table (exluding the remove button),
        and the new state (include/exclude)
        """
        data = []
        for name, values in filters.items():
            data.append({'Name_' + TIME_TABLE: name,
                         'Start_' + TIME_TABLE: values["start"],
                         'End_' + TIME_TABLE: values["end"]})

        return data
