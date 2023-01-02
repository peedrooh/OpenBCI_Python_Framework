from __future__ import annotations
import abc
from typing import List, Dict, Final, Any

from models.exception.invalid_parameter_value import InvalidParameterValue
from models.framework_data import FrameworkData


# TODO Isolamento de nodes em threads separadas. Cada nó deve ser executado em uma thread
class Node:
    _MODULE_NAME: Final[str] = 'models.node'
    """Abstract base class for processing pipeline execution on this framework.
    """

    def __init__(self, parameters=None) -> None:
        super().__init__()
        self._validate_parameters(parameters)
        self.parameters = parameters
        self._initialize_buffer_options(parameters['buffer_options'])
        self._type: Final[str] = parameters['type']
        self.name: Final[str] = parameters['name']
        self._clear_input_buffer()
        self._clear_output_buffer()

        self._initialize_children()

        self._child_input_relation: Dict[Node, List[str]] = {}

    @abc.abstractmethod
    def _validate_parameters(self, parameters: dict):
        if 'module' not in parameters:
            raise ValueError("error"
                             ".missing"
                             ".node"
                             ".module")
        if 'models.node.' not in parameters['module']:
            ValueError('error'
                       '.invalid'
                       '.value'
                       '.node'
                       '.module')
        if 'type' not in parameters:
            raise ValueError("error"
                             ".missing"
                             ".node"
                             ".type")

        if 'buffer_options' not in parameters:
            raise ValueError('error'
                             '.missing'
                             '.node'
                             '.buffer_options')

        if 'outputs' not in parameters:
            raise ValueError('error'
                             '.missing'
                             '.node'
                             '.outputs')

        if 'name' not in parameters:
            raise ValueError('error'
                             '.missing'
                             '.node'
                             '.name')

    def _clear_input_buffer(self):
        """Sets input buffer to new empty object for each input name
        """
        self._input_buffer = {}
        for input_name in self._get_inputs():
            self._input_buffer[input_name] = FrameworkData()

    def _clear_output_buffer(self):
        """Sets output buffer to new empty object for each output name
        """
        self._output_buffer = {}
        for output_name in self._get_outputs():
            self._output_buffer[output_name] = FrameworkData()

    @staticmethod
    def _insert_data_in_buffer(data: FrameworkData, buffer_data_name: str, buffer: Dict[str, FrameworkData]):
        buffer[buffer_data_name].extend(data)

    def _insert_new_input_data(self, data: FrameworkData, input_name: str):
        """Appends new data to the end of already existing input buffer

        :param data: Data to be added. Should be in channel X sample format
        :type data: FrameworkData
        :param input_name: Node input name.
        :type input_name: str
        """
        self._input_buffer[input_name].extend(data)

    def _insert_new_output_data(self, data: FrameworkData, output_name: str):
        """Appends new data to the end of already existing output buffer

        :param data: Data to be added. Should be in channel X sample format
        :type data: FrameworkData
        :param output_name: Node output name.
        :type output_name: str
        """
        self._output_buffer[output_name].extend(data)

    def _initialize_children(self):
        """Sets child nodes dictionary to a new, empty dict
        """
        self._children: Dict[str, List[Dict[str, Any]]] = {}
        for output_name in self._get_outputs():
            self._children[output_name] = []

    def add_child(self, output_name: str, node: Node, input_name: str):
        """Adds a new child node to child nodes dictionary

        :param output_name: Current node output name, used as key.
        :type output_name: str
        :param node: Child node object.
        :type node: Node
        :param input_name: Child node input name.
        :type input_name: str
        """
        # TODO Melhorar o objeto guardado em self._children
        if node not in self._child_input_relation:
            self._child_input_relation[node] = []
        if input_name in self._child_input_relation[node]:
            raise InvalidParameterValue(module='node', parameter=f'outputs.{output_name}', cause='already_added')
        self._children[output_name].append(
            {
                'node': node,
                'run': lambda data: node.run(data, input_name),
                'dispose': lambda x: node.dispose()
            }
        )

    def _dispose_all_children(self):
        for output_name in self._get_outputs():
            output_children = self._children[output_name]
            for child in output_children:
                child['dispose'](child)

    def _call_children(self):
        """Calls child nodes to execute their processing given current node output buffer content.
        """
        for output_name in self._get_outputs():
            output = self._output_buffer[output_name]
            output_children = self._children[output_name]
            for child in output_children:
                child['run'](output)

    def run(self, data: FrameworkData = None, input_name: str = None) -> None:
        """Run node main function

        :param data: Node input data (channel X sample). Can be None if node takes no input data.
        :type data: FrameworkData
        :param input_name: Node input name. Can be None if node takes no input data.
        :type input_name: str
        """
        self._run(data, input_name)
        if not self._is_next_node_call_enabled():
            return
        self._call_children()

    def check_input(self, input_name: str) -> None:
        if input_name not in self._get_inputs():
            raise ValueError('error'
                             '.invalid'
                             '.value'
                             '.node'
                             '.input')

    def check_output(self, output_name: str) -> None:
        if output_name not in self._get_outputs():
            raise ValueError('error'
                             '.invalid'
                             '.value'
                             '.node'
                             '.output')

    @classmethod
    @abc.abstractmethod
    def from_config_json(cls, parameters: dict):
        """Returns node instance from given parameters in dict form

        :param parameters: Node parameters in dict form.
        :type parameters: dict
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _run(self, data: FrameworkData, input_name: str) -> None:
        """Node self implementation of processing on input data

        :param data: Node input data.
        :type data: FrameworkData
        :param input_name: Node input name.
        :type input_name: str
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _is_next_node_call_enabled(self) -> bool:
        """Node self implementation to check if child nodes should be called.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _initialize_buffer_options(self, buffer_options: dict) -> None:
        """Node self implementation of buffer behaviour options initialization

        :param buffer_options: Buffer behaviour options.
        :type buffer_options: dict
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_inputs(self) -> List[str]:
        """Returns the input names in list form.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _get_outputs(self) -> List[str]:
        """Returns the output names in list form.
        """
        raise NotImplementedError()

    def dispose_all(self) -> None:
        """Disposes itself and all its children nodes
        """
        self._dispose_all_children()
        self.dispose()

    @abc.abstractmethod
    def dispose(self) -> None:
        """Node self implementation of disposal of allocated resources.
        """
        raise NotImplementedError()
