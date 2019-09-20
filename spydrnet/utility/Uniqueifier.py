import collections
import sys

from spydrnet.ir import *
import spydrnet.utility.utility as util

class Uniquifier:

    def __init__(self):
        self.definition_count = dict()
        self.original_inner_pin_to_new_inner_pin = dict()
        self.port_map = dict()
        self.instance_map = dict()
        self.outer_pin_map = dict()
        self.definition_copies = dict()
        pass

    def run(self, ir):
        reverse_topological_order = self._get_reverse_topological_order(ir)
        for definition in reverse_topological_order:
            self._make_definition_copies(definition, self.definition_count[definition] - 1)
        self._clean(ir.libraries[1].definitions[-1])
        

    def _get_reverse_topological_order(self, ir):
        top_def = ir.top_instance.definition
        depth_first_search = collections.deque()
        for instance in top_def.instances:
            # test = list(instance.outer_pins.keys())[0].wire
            # if list(instance.outer_pins.keys())[0].wire is not None:
            if not util.is_leaf(instance):
                depth_first_search.extend(self._trace_definition(instance.definition))

        visited = set()
        reverse_topological_order = list()
        while len(depth_first_search) != 0:
            definition = depth_first_search.popleft()
            if definition not in visited:
                visited.add(definition)
                reverse_topological_order.append(definition)
        for definition, value in self.definition_count.items():
            # print('Definition ' + definition.__getitem__('EDIF.identifier') + ' was used ' + str(value) + ' times')
            pass
        return reverse_topological_order

    def _trace_definition(self, definition):
        top_order = collections.deque()
        for instance in definition.instances:
            if len(instance.outer_pins) == 0:
                return top_order
            inner_pin = list(instance.outer_pins.keys())[0]
            if inner_pin.wire is None:
                continue
            top_order.extend(self._trace_definition(instance.definition))
        top_order.append(definition)
        self._increment_definition_count(definition)
        return top_order

    def _increment_definition_count(self, definition):
        if definition not in self.definition_count:
            self.definition_count[definition] = 1
        else:
            self.definition_count[definition] += 1

    def _make_definition_copies(self, def_to_copy, num_of_copies):
        copies = dict()
        copies[def_to_copy] = collections.deque()
        self.definition_copies[def_to_copy] = list()
        for i in range(num_of_copies):
            def_copy = Definition()
            self._copy_metadata(def_to_copy, def_copy, i)
            self._copy_ports(def_to_copy, def_copy)
            self._copy_instances(def_to_copy, def_copy)
            self._copy_cable(def_to_copy, def_copy)
            self.definition_copies[def_to_copy].append(def_copy)
            for y in range(len(def_to_copy.library.definitions)):
                if def_to_copy == def_to_copy.library.definitions[y]:
                    break
            try:
                def_to_copy.library.add_definition(def_copy, y)
            except KeyError:
                name = def_to_copy['EDIF.identifier']
                message = 'Try to add a definition with name of ' + name + 'but the name was already use'
                raise KeyError(message)
        self._definition_clean_up(def_to_copy)
        return self.definition_copies

    def _copy_ports(self, def_to_copy, def_copy):
        for port_to_copy in def_to_copy.ports:
            port_copy = def_copy.create_port()
            self._copy_metadata(port_to_copy, port_copy)
            port_copy.direction = port_to_copy.direction
            for inner_pin_to_copy in port_to_copy.inner_pins:
                self.original_inner_pin_to_new_inner_pin[inner_pin_to_copy] = port_copy.create_pin()
            if hasattr(port_to_copy, 'is_array'):
                port_copy.is_array = port_to_copy.is_array
                self.port_map[port_to_copy] = port_copy

    def _copy_instances(self, def_to_copy, def_copy):
        for instance_to_copy in def_to_copy.instances:
            instance_copy = def_copy.create_instance()
            self._copy_metadata(instance_to_copy, instance_copy)
            for inner_pin, outer_pin_to_copy in instance_to_copy.outer_pins.items():
                outer_pin_copy = OuterPin()
                outer_pin_copy.instance = instance_copy
                outer_pin_copy.inner_pin = inner_pin
                instance_copy.outer_pins[inner_pin] = outer_pin_copy
                self.outer_pin_map[outer_pin_to_copy] = outer_pin_copy
            instance_copy.definition = instance_to_copy.definition
            if inner_pin.wire is not None:
                self._make_instances_unique(instance_copy)
            self.instance_map[instance_to_copy] = instance_copy

    def _copy_cable(self, def_to_copy, def_copy):
        for cable_to_copy in def_to_copy.cables:
            cable_copy = def_copy.create_cable()
            self._copy_metadata(cable_to_copy, cable_copy)
            for wire_to_copy in cable_to_copy.wires:
                wire_copy = cable_copy.create_wire()
                self._copy_wire(wire_to_copy, wire_copy)

    def _copy_wire(self, wire_to_copy, wire_copy):
        for pin in wire_to_copy.pins:
            if isinstance(pin, InnerPin):
                wire_copy.connect_pin(self.original_inner_pin_to_new_inner_pin[pin])
            else:
                wire_copy.connect_pin(self.outer_pin_map[pin])

    def _definition_clean_up(self, definition):
        if definition in self.definition_copies:
            for instance in definition.instances:
                if instance.definition in self.definition_copies:
                    self._make_instances_unique(instance)
                    

    def _clean(self, definition):
        for instance in definition.instances:
            if instance.definition in self.definition_copies:
                self._make_instances_unique(instance)

    def _make_instances_unique(self, instance_copy):
        if len(self.definition_copies[instance_copy.definition]) == 0:
            return
        definition = self.definition_copies[instance_copy.definition].pop()
        temp = dict()
        for inner_pin, outer_pin in instance_copy.outer_pins.items():
            for i in range(len(inner_pin.port.inner_pins)):
                if inner_pin == inner_pin.port.inner_pins[i]:
                    break
            for new_port in definition.ports:
                if new_port.__getitem__('EDIF.identifier') == inner_pin.port.__getitem__('EDIF.identifier'):
                    break
            outer_pin.inner_pin = new_port.inner_pins[i]
            inner_pin = new_port.inner_pins[i]
            temp[inner_pin] = outer_pin
        instance_copy.definition = definition
        instance_copy.outer_pins = temp

    def _copy_metadata(self, original, copy, copy_num=None):
        for key, data in original._metadata.items():
            copy.__setitem__(key, data)
        if type(original) is Definition:
            if 'EDIF.identifier' in copy._metadata:
                while copy._metadata['EDIF.identifier'] + '_UNIQUE_' + str(copy_num) in self.definition_count:
                    copy_num += 1
                self.definition_count[copy._metadata['EDIF.identifier'] + '_UNIQUE_' + str(copy_num)] = 1
                copy._metadata['EDIF.identifier'] = copy._metadata['EDIF.identifier'] + '_UNIQUE_' + str(copy_num)
            if 'EDIF.original_identifier' in copy._metadata:
                copy._metadata['EDIF.original_identifier'] = copy._metadata['EDIF.original_identifier'] + \
                                                             '_UNIQUE_' + str(copy_num)

from spydrnet.parsers.edif.parser import EdifParser
from spydrnet.composers.edif.composer import ComposeEdif
import spydrnet.support_files as files
if __name__ == '__main__':
    if len(sys.argv) > 1:
        if len(sys.argv) != 3:
            sys.exit("If using arguments, must only have an input file and output file")
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = files.edif_files['riscv_multi_core.edf']
        output_file = 'riscv_multi_core_out.edf'
    parser = EdifParser.from_filename(input_file)
    parser.parse()
    ir = parser.netlist
    uniquifer = Uniquifier()
    uniquifer.run(ir)
    ir = ir
    composer = ComposeEdif()
    composer.run(ir, output_file)
    pass