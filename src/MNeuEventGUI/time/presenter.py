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
    def __init__(self):
        """
        This creates the presenter object for the
        widget.
        """
        self._previous = 'Exclude'

        # create columns
        name = TextColumn('Name_' + TIME_TABLE, 'Name')

        start = NumericColumn('Start_' + TIME_TABLE, 'Start')
        end = NumericColumn('End_' + TIME_TABLE, 'End')

        cols = TableColumns([TableGroup([name]),
                             TableGroup([start,
                                         end],
                                        'Exclude Filter details')],
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

    def set_time_range(self, start, end):
        """
        Sets the range of allowed times
        :param start: the start time for the data
        :param end: the end time for the data
        """
        self.start = start
        self.end = end
        self.cols.set_range(start, end)

    def validate_row(self, change, data):
        """
        A validation check for the table.
        It has a rule that each row name
        must be unique.
        :param change: the change in the table (row)
        :param data: the table data as a list of rows (dicts)
        :returns: the updated data and the error message
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
        return data, msg

    @property
    def default_row(self):
        """
        The code needed to create a default
        row for the time table
        :returns: dict of the values for the time table.
        """
        return {'Start_' + TIME_TABLE: 0.33 * self.end,
                'End_' + TIME_TABLE: 0.66 * self.end}

    def get_range(self, data):
        """
        Gets the x range from the time table data.
        Used for creating shaded region for the row
        :peram data' The row data from the table
        :returns: the start and end values
        """
        return [data['Start_' + TIME_TABLE], data['End_' + TIME_TABLE]]

    def set_state(self, value):
        """
        Sets the group name in the table
        :param value: the updated part of the table name
        (expect either Include or Exclude)
        """
        self.cols.set_title(2, f'{value} Filter details')

    def load(self, filters: list[dict]):
        """
        A method to load filters from a TimeFilters object.
        :param filters: the dataclass of time filters.
        :returns: a list of the row details
        for the time table (exluding the remove button),
        and the new state (include/exclude)
        """

        data = []
        for f in filters:
            data.append({'Name_' + TIME_TABLE: f["name"],
                         'Start_' + TIME_TABLE: f["start"],
                         'End_' + TIME_TABLE: f["end"]})

        return data
