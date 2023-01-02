import os
import csv
from typing import List, Dict, Final

from models.exception.invalid_parameter_value import InvalidParameterValue
from models.exception.missing_parameter import MissingParameterError
from models.framework_data import FrameworkData
from models.node.generator.generator_node import GeneratorNode


class CSVFile(GeneratorNode):
    _MODULE_NAME: Final[str] = 'node.generator.file.csvfile'

    OUTPUT_MAIN: Final[str] = 'main'
    OUTPUT_TIMESTAMP: Final[str] = 'timestamp'

    def __init__(self, parameters: dict) -> None:
        super().__init__(parameters)
        self._validate_parameters(parameters)
        self.sampling_frequency = parameters['sampling_frequency']
        self.file_path = parameters['file_path']
        self.channel_column_names = parameters['channel_column_names'] \
            if 'channel_column_names' in parameters \
            else None
        self.timestamp_column_name = parameters['timestamp_column_name'] \
            if 'timestamp_column_name' in parameters \
            else None
        self._init_csv_reader()

    def _validate_parameters(self, parameters: dict):
        if 'sampling_frequency' not in parameters:
            raise MissingParameterError(module=self._MODULE_NAME,
                                        parameter='sampling_frequency')
        if 'file_path' not in parameters:
            raise MissingParameterError(module=self._MODULE_NAME,
                                        parameter='file_path')
        if type(parameters['sampling_frequency']) is not float and type(parameters['sampling_frequency']) is not int:
            raise InvalidParameterValue(module=self._MODULE_NAME,
                                        parameter='sampling_frequency',
                                        cause='must_be_number')
        if type(parameters['file_path']) is not str:
            raise InvalidParameterValue(module=self._MODULE_NAME,
                                        parameter='file_path',
                                        cause='must_be_string')
        if os.path.splitext(parameters['file_path'])[1] != '.csv':
            raise InvalidParameterValue(module=self._MODULE_NAME,
                                        parameter='file_path',
                                        cause='must_be_csv_file')
        if 'timestamp_column_name' in parameters and type(parameters['timestamp_column_name']) is not str:
            raise InvalidParameterValue(module=self._MODULE_NAME,
                                        parameter='timestamp_column_name',
                                        cause='must_be_string')

        if 'channel_column_names' in parameters:
            if type(parameters['channel_column_names']) is not list:
                raise InvalidParameterValue(module=self._MODULE_NAME,
                                            parameter='channel_column_names',
                                            cause='must_be_list')
            if len(parameters['channel_column_names']) < 1:
                raise InvalidParameterValue(module=self._MODULE_NAME,
                                            parameter='channel_column_names',
                                            cause='is_empty')
            if any(type(element) is not str for element in parameters['channel_column_names']):
                raise InvalidParameterValue(module=self._MODULE_NAME,
                                            parameter='channel_column_names',
                                            cause='must_contain_strings_only')

    @classmethod
    def from_config_json(cls, parameters: dict):
        return cls(parameters=parameters)

    def _init_csv_reader(self) -> None:
        self._csv_file = open(self.file_path)
        self._csv_file.close()
        self._csv_file = open(self.file_path)
        self._csv_reader = csv.DictReader(self._csv_file)

    def _should_generate_timestamp(self) -> bool:
        return self.timestamp_column_name is None

    def _is_next_node_call_enabled(self) -> bool:
        return self._output_buffer[self.OUTPUT_TIMESTAMP].has_data()

    def _is_generate_data_condition_satisfied(self) -> bool:
        return not self._csv_file.closed

    def _generate_data(self) -> Dict[str, FrameworkData]:
        main_data = FrameworkData(self.sampling_frequency, self.channel_column_names)
        timestamp_data = FrameworkData(self.sampling_frequency)
        for row_index, row in enumerate(self._csv_reader):
            if row_index == 0 and self.channel_column_names is None:
                self.channel_column_names = row.keys()
            for channel_name in self.channel_column_names:
                main_data.input_data_on_channel(channel_name, [float(row[channel_name])])
            row_timestamp = row_index if self._should_generate_timestamp() else row[self.timestamp_column_name]
            timestamp_data.input_data_on_channel(data=[row_timestamp])
        self._csv_file.close()

        print(f'{self.file_path} closed')
        return {
            self.OUTPUT_MAIN: main_data,
            self.OUTPUT_TIMESTAMP: timestamp_data
        }

    def _get_outputs(self) -> List[str]:
        return [
            self.OUTPUT_MAIN,
            self.OUTPUT_TIMESTAMP
        ]

    def dispose(self) -> None:
        self._clear_output_buffer()
        self._clear_input_buffer()
        if self._csv_file is not None and not self._csv_file.closed:
            self._csv_file.close()
