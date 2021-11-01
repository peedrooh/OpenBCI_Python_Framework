from brainflow import DataFilter, DetrendOperations

from models.preprocessing.node import PreProcessingNode


class Detrend(PreProcessingNode):
    def __init__(self, parameters: dict) -> None:
        super().__init__(parameters)
        if 'type' not in parameters:
            raise Exception('preprocessing.detrend.invalid.parameters.must.have.type')
        self._type = parameters['type']
        self._detrend_type: DetrendOperations = DetrendOperations[self._type]
        self.process = self._set_detrend

    def _set_detrend(self, data):
        DataFilter.detrend(data, self._detrend_type)
