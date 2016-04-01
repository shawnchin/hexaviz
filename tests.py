# Copyright (c) 2015 Shawn Chin

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import json
import unittest

from hexaviz import Mesh, render, render_mesh_as_dot
from hexaviz import DuplicateEntry, InvalidComponent, InvalidPort, InvalidConnection, InvalidResource


class MeshTest(unittest.TestCase):

    def test_empty_mesh_still_returns_valid_data(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN we request a dict representation of the mesh
        data = m.as_dict()

        # THEN a valid empty representation is returned
        self.assertEqual({'components': [], 'connections': [], 'resources': []}, data)

    def test_added_component_can_be_retrieved_from_mesh(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN I add a component
        m.add_component('Component A')

        # THEN that component is represented in the output
        self.assertEqual({
            'components': [
                {'name': 'Component A', 'needs_ports': [], 'provides_ports': []},
            ],
            'resources': [],
            'connections': [],
        }, m.as_dict())

    def test_components_are_returned_in_the_order_they_were_added(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN I add several component
        m.add_component('Component A')
        m.add_component('Component Z')
        m.add_component('Component M')

        # THEN that component are presented in the order they were added
        self.assertEqual({
            'components': [
                {'name': 'Component A', 'needs_ports': [], 'provides_ports': []},
                {'name': 'Component Z', 'needs_ports': [], 'provides_ports': []},
                {'name': 'Component M', 'needs_ports': [], 'provides_ports': []},
            ],
            'resources': [],
            'connections': [],
        }, m.as_dict())

    def test_DuplicateEntry_exception_raised_when_adding_components_with_same_name(self):
        # GIVEN a Mesh with existing components
        m = Mesh()
        m.add_component('Component A')
        m.add_component('Component Z')

        # WHEN we attempt to add a component with the same name
        # THEN a DuplicateEntry exception is raised
        self.assertRaises(DuplicateEntry, m.add_component, 'Component A')

    def test_adding_needs_port_to_existing_component(self):
        # GIVEN a Mesh with existing component
        m = Mesh()
        m.add_component('Component A')

        # WHEN we add a needs port to the component
        m.add_needs_port('Component A', 'needs 1')

        # THEN the needs port is represented in the output
        self.assertEqual({
            'components': [
                {
                    'name': 'Component A',
                    'needs_ports': ['needs 1'],
                    'provides_ports': []
                },
            ],
            'resources': [],
            'connections': [],
        }, m.as_dict())

    def test_adding_provides_port_to_existing_component(self):
        # GIVEN a Mesh with existing component
        m = Mesh()
        m.add_component('Component A')

        # WHEN we add a provides port to the component
        m.add_provides_port('Component A', 'provides 1')

        # THEN the provides port is represented in the output
        self.assertEqual({
            'components': [
                {
                    'name': 'Component A',
                    'needs_ports': [],
                    'provides_ports': ['provides 1']
                },
            ],
            'resources': [],
            'connections': [],
        }, m.as_dict())

    def test_adding_needs_port_when_components_are_created(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN I add a component with needs ports
        m.add_component('Component A', needs_ports=['needs 1', 'needs 2'])

        # THEN the needs ports are represented in the output
        self.assertEqual({
            'components': [
                {
                    'name': 'Component A',
                    'needs_ports': ['needs 1', 'needs 2'],
                    'provides_ports': []
                },
            ],
            'resources': [],
            'connections': [],
        }, m.as_dict())

    def test_adding_provides_port_when_components_are_created(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN I add a component with provides ports
        m.add_component('Component A', provides_ports=['provides 1', 'provides 2'])

        # THEN the provides ports are represented in the output
        self.assertEqual({
            'components': [
                {
                    'name': 'Component A',
                    'needs_ports': [],
                    'provides_ports': ['provides 1', 'provides 2'],
                },
            ],
            'resources': [],
            'connections': [],
        }, m.as_dict())

    def test_ports_are_returned_in_the_order_they_were_added(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN I add a component with ports in a specific order
        m.add_component('Component A',
                        needs_ports=['needs 8', 'needs 7'],
                        provides_ports=['provides 8', 'provides 7'])
        m.add_needs_port('Component A', 'needs 1')
        m.add_provides_port('Component A', 'provides 1')

        # THEN the ports are represented in the output in the same order they were entered
        self.assertEqual({
            'components': [
                {
                    'name': 'Component A',
                    'needs_ports': ['needs 8', 'needs 7', 'needs 1'],
                    'provides_ports': ['provides 8', 'provides 7', 'provides 1'],
                },
            ],
            'resources': [],
            'connections': [],
        }, m.as_dict())

    def test_DuplicateEntry_exception_raised_when_adding_needs_port_with_same_name(self):
        # GIVEN a Mesh with existing components that has needs and provides
        m = Mesh()
        m.add_component('Component A', needs_ports=['needs 1'], provides_ports=['provides 1'])

        # WHEN we attempt to add an existing needs port to the component
        # THEN a DuplicateEntry exception is raised
        self.assertRaises(DuplicateEntry, m.add_needs_port, 'Component A', 'needs 1')

    def test_DuplicateEntry_exception_raised_when_adding_provides_port_with_same_name(self):
        # GIVEN a Mesh with existing components that has needs and provides
        m = Mesh()
        m.add_component('Component A', needs_ports=['needs 1'], provides_ports=['provides 1'])

        # WHEN we attempt to add an existing provides port to the component
        # THEN a DuplicateEntry exception is raised
        self.assertRaises(DuplicateEntry, m.add_provides_port, 'Component A', 'provides 1')

    def test_adding_connection_between_two_ports(self):
        # GIVEN the following components
        #
        #     _____________        _____________
        #    |      A      |      |      B      |
        #    |-------------|      |-------------|
        #    |      |  n1  |      |  p1  |      |
        #    |______|______|      |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])

        # WHEN we add a connection between A:n1 and B:p1
        m.add_connection('A', 'n1', 'B', 'p1')

        # THEN we get the following mesh representation
        #
        #     _____________        _____________
        #    |      A      |      |      B      |
        #    |-------------|      |-------------|
        #    |      |  n1  | ---> |  p1  |      |
        #    |______|______|      |______|______|
        #
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': [], 'provides_ports': ['p1']},
            ],
            'resources': [],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
            ],
        }, m.as_dict())

    def test_multiple_connection_can_be_made_to_the_same_producer_port(self):
        # GIVEN the following components
        #
        #     _____________            _____________
        #    |      A      |          |      B      |
        #    |-------------|          |-------------|
        #    |      |  n1  |          |  p1  |      |
        #    |______|______|          |______|______|
        #
        #
        #     _____________
        #    |      C      |
        #    |-------------|
        #    |      |  nX  |
        #    |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])
        m.add_component('C', needs_ports=['nX'])

        # WHEN we add a connection between A:n1 and B:p1
        # WHEN we add a connection between C:nX and B:p1
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection('C', 'nX', 'B', 'p1')

        # THEN we get the following mesh representation
        #
        #     _____________            _____________
        #    |      A      |          |      B      |
        #    |-------------|          |-------------|
        #    |      |  n1  |-----+--->|  p1  |      |
        #    |______|______|     |    |______|______|
        #                        |
        #                        |
        #     _____________      |
        #    |      C      |     |
        #    |-------------|     |
        #    |      |  nX  |-----+
        #    |______|______|
        #
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': [], 'provides_ports': ['p1']},
                {'name': 'C', 'needs_ports': ['nX'], 'provides_ports': []},
            ],
            'resources': [],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
                {
                    'consumer_component': 'C',
                    'consumer_port': 'nX',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
            ],
        }, m.as_dict())

    def test_multiple_connections_across_components_with_multiple_ports(self):
        # GIVEN the following components
        #
        #     _____________            _____________
        #    |      A      |          |      B      |
        #    |-------------|          |-------------|
        #    |      |  n1  |          |  p1  |      |
        #    |      |______|          |______|      |
        #    |      |  n2  |          |  p2  |      |
        #    |______|______|          |______|______|
        #
        #
        #     _____________            _____________
        #    |      C      |          |      D      |
        #    |-------------|          |-------------|
        #    |      |  nX  |          |  pX  |      |
        #    |______|______|          |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1', 'n2'])
        m.add_component('B', provides_ports=['p1', 'p2'])
        m.add_component('C', needs_ports=['nX'])
        m.add_component('D', provides_ports=['pX'])

        # WHEN we add a connection between A:n1 and B:p1
        # WHEN we add a connection between C:nX and B:p1
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection('A', 'n2', 'D', 'pX')
        m.add_connection('C', 'nX', 'B', 'p2')

        # THEN we get the following mesh representation
        #
        #     _____________              _____________
        #    |      A      |            |      B      |
        #    |-------------|            |-------------|
        #    |      |  n1  |----------->|  p1  |      |
        #    |      |______|            |______|      |
        #    |      |  n2  |-----+  +-->|  p2  |      |
        #    |______|______|     |  |   |______|______|
        #                     +- | -+
        #                     |  |
        #     _____________   |  |      _____________
        #    |      C      |  |  |     |      D      |
        #    |-------------|  |  |     |-------------|
        #    |      |  nX  |--+  +---->|  pX  |      |
        #    |______|______|           |______|______|
        #
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1', 'n2'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': [], 'provides_ports': ['p1', 'p2']},
                {'name': 'C', 'needs_ports': ['nX'], 'provides_ports': []},
                {'name': 'D', 'needs_ports': [], 'provides_ports': ['pX']},
            ],
            'resources': [],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n2',
                    'producer_component': 'D',
                    'producer_port': 'pX',
                },
                {
                    'consumer_component': 'C',
                    'consumer_port': 'nX',
                    'producer_component': 'B',
                    'producer_port': 'p2',
                },
            ],
        }, m.as_dict())

    def test_InvalidComponent_exception_raised_when_creating_connections_with_invalid_consumer_component(self):
        # GIVEN the following components
        #
        #     _____________        _____________
        #    |      A      |      |      B      |
        #    |-------------|      |-------------|
        #    |      |  n1  |      |  p1  |      |
        #    |______|______|      |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])

        # WHEN creating a component between X:n1 and B:p1
        # THEN an InvalidComponent exception is raised
        self.assertRaises(InvalidComponent, m.add_connection, 'X', 'n1', 'B', 'p1')

    def test_InvalidComponent_exception_raised_when_creating_connections_with_invalid_producer_component(self):
        # GIVEN the following components
        #
        #     _____________        _____________
        #    |      A      |      |      B      |
        #    |-------------|      |-------------|
        #    |      |  n1  |      |  p1  |      |
        #    |______|______|      |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])

        # WHEN creating a component between A:n1 and X:p1
        # THEN an InvalidComponent exception is raised
        self.assertRaises(InvalidComponent, m.add_connection, 'A', 'n1', 'X', 'p1')

    def test_InvalidPort_exception_raised_when_creating_connections_with_invalid_consumer_port(self):
        # GIVEN the following components
        #
        #     _____________        _____________
        #    |      A      |      |      B      |
        #    |-------------|      |-------------|
        #    |      |  n1  |      |  p1  |      |
        #    |______|______|      |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])

        # WHEN creating a component between A:p1 and B:p1
        # THEN an InvalidPort exception is raised
        self.assertRaises(InvalidPort, m.add_connection, 'A', 'p1', 'B', 'p1')

    def test_InvalidPort_exception_raised_when_creating_connections_with_invalid_producer_port(self):
        # GIVEN the following components
        #
        #     _____________        _____________
        #    |      A      |      |      B      |
        #    |-------------|      |-------------|
        #    |      |  n1  |      |  p1  |      |
        #    |______|______|      |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])

        # WHEN creating a component between A:n1 and B:n1
        # THEN an InvalidPort exception is raised
        self.assertRaises(InvalidPort, m.add_connection, 'A', 'n1', 'B', 'n1')

    def test_DuplicateEntry_exception_raised_when_assigning_multiple_connections_to_the_same_needs_port(self):
        # GIVEN the following mesh
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |      |
        #    |______|______|         |______|______|
        #
        #                             _____________
        #                            |      D      |
        #                            |-------------|
        #                            |  pX  |      |
        #                            |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])
        m.add_component('D', provides_ports=['pX'])
        m.add_connection('A', 'n1', 'B', 'p1')

        # WHEN attempting to create the following invalid connections
        #     _____________             _____________
        #    |      A      |           |      B      |
        #    |-------------|           |-------------|
        #    |      |  n1  |----+----->|  p1  |      |
        #    |______|______|    |      |______|______|
        #                       |
        #                    INVALID    _____________
        #                       |      |      D      |
        #                       |      |-------------|
        #                       +----->|  pX  |      |
        #                              |______|______|
        #
        # THEN an InvalidConnection exception is raised
        self.assertRaises(InvalidConnection, m.add_connection, 'A', 'n1', 'D', 'pX')

    def test_added_resource_can_be_retrieved_from_mesh(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN I add a resource
        m.add_resource('Resource X')

        # THEN that resource is represented in the output
        self.assertEqual({
            'components': [],
            'resources': ['Resource X'],
            'connections': [],
        }, m.as_dict())

    def test_resources_are_returned_in_the_order_they_were_added(self):
        # GIVEN a new Mesh instance
        m = Mesh()

        # WHEN I add several resources
        m.add_resource('Resource X')
        m.add_resource('Resource Z')
        m.add_resource('Resource Y')

        # THEN that resources are presented in the order they were added
        self.assertEqual({
            'components': [],
            'resources': ['Resource X', 'Resource Z', 'Resource Y'],
            'connections': [],
        }, m.as_dict())

    def test_DuplicateEntry_exception_raised_when_adding_resources_with_same_name(self):
        # GIVEN a Mesh with existing resource
        m = Mesh()
        m.add_resource('Resource X')

        # WHEN we attempt to add a resource with the same name
        # THEN a DuplicateEntry exception is raised
        self.assertRaises(DuplicateEntry, m.add_resource, 'Resource X')

    def test_adding_connection_from_port_to_edge_resource(self):
        # GIVEN a mesh with the following component and resource
        #
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |            [ Resource X ]
        #    |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_resource('Resource X')

        # WHEN we connect A:n1 to Resource X
        m.add_connection_to_resource('A', 'n1', 'Resource X')

        # THEN we get the following mesh representation
        #
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |--------->[ Resource X ]
        #    |______|______|
        #
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1'], 'provides_ports': []},
            ],
            'resources': ['Resource X'],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'resource': 'Resource X',
                },
            ],
        }, m.as_dict())

    def test_InvalidComponent_exception_raised_when_creating_connections_to_resource_with_invalid_consumer_component(self):
        # GIVEN a mesh with the following component and resource
        #
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |            [ Resource X ]
        #    |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_resource('Resource X')

        # WHEN creating a component between X:n1 and Resource X
        # THEN an InvalidComponent exception is raised
        self.assertRaises(InvalidComponent, m.add_connection_to_resource, 'X', 'n1', 'Resource X')

    def test_InvalidPort_exception_raised_when_creating_connections_to_resource_with_invalid_consumer_port(self):
        # GIVEN a mesh with the following component and resource
        #
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |            [ Resource X ]
        #    |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_resource('Resource X')

        # WHEN creating a component between A:nX and Resource X
        # THEN an InvalidPort exception is raised
        self.assertRaises(InvalidPort, m.add_connection_to_resource, 'A', 'nX', 'Resource X')

    def test_InvalidResource_exception_raised_when_creating_connections_to_resource_that_does_not_exist(self):
        # GIVEN a mesh with the following component and resource
        #
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |            [ Resource X ]
        #    |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_resource('Resource X')

        # WHEN creating a component between A:n1 and Resource P
        # THEN an InvalidResource exception is raised
        self.assertRaises(InvalidResource, m.add_connection_to_resource, 'A', 'n1', 'Resource P')

    def test_DuplicateEntry_exception_raised_when_connecting_already_connected_port_to_a_resource(self):
        # GIVEN the following mesh
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |      |
        #    |______|______|         |______|______|
        #
        #
        #                             [ Resource X ]
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', provides_ports=['p1'])
        m.add_resource('Resource X')
        m.add_connection('A', 'n1', 'B', 'p1')

        # WHEN attempting to create the following invalid connections
        #     _____________             _____________
        #    |      A      |           |      B      |
        #    |-------------|           |-------------|
        #    |      |  n1  |----+----->|  p1  |      |
        #    |______|______|    |      |______|______|
        #                       |
        #                    INVALID
        #                       |
        #                       |
        #                       +----->[ Resource X ]
        #
        #
        # THEN an InvalidConnection exception is raised
        self.assertRaises(InvalidConnection, m.add_connection_to_resource, 'A', 'n1', 'Resource X')

    def test_DuplicateEntry_exception_raised_when_adding_connection_to_port_already_connected_to_resource(self):
        # GIVEN the following mesh
        #
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |-------->[ Resource X ]
        #    |______|______|
        #
        #                             _____________
        #                            |      D      |
        #                            |-------------|
        #                            |  pX  |      |
        #                            |______|______|
        #
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('D', provides_ports=['pX'])
        m.add_resource('Resource X')
        m.add_connection_to_resource('A', 'n1', 'Resource X')

        # WHEN attempting to create the following invalid connections
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |----+----->[ Resource X ]
        #    |______|______|    |
        #                       |
        #                    INVALID    _____________
        #                       |      |      D      |
        #                       |      |-------------|
        #                       +----->|  pX  |      |
        #                              |______|______|
        #
        # THEN an InvalidConnection exception is raised
        self.assertRaises(InvalidConnection, m.add_connection, 'A', 'n1', 'D', 'pX')

    def test_component_can_be_highlighted(self):
        # GIVEN the following mesh
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |  n2  |--------->[ Resource X ]
        #    |______|______|         |______|______|
        #
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', needs_ports=['n2'], provides_ports=['p1'])
        m.add_resource('Resource X')
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection_to_resource('B', 'n2', 'Resource X')

        # WHEN component B is highlighted
        m.highlight_component('B')

        # THEN this is reflected in the dict representation
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': ['n2'], 'provides_ports': ['p1'], 'highlighted': True}
            ],
            'resources': ['Resource X'],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
                {
                    'consumer_component': 'B',
                    'consumer_port': 'n2',
                    'resource': 'Resource X',
                },
            ],
        }, m.as_dict())

    def test_InvalidComponent_exception_raised_when_highlighting_unknown_component(self):
        # GIVEN a mesh with the following component and resource
        #
        #     _____________
        #    |      A      |
        #    |-------------|
        #    |      |  n1  |            [ Resource X ]
        #    |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_resource('Resource X')

        # WHEN unknown component Y
        # THEN an InvalidComponent exception is raised
        self.assertRaises(InvalidComponent, m.highlight_component, 'Y')

    def test_connection_can_be_highlighted(self):
        # GIVEN the following mesh
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |  n2  |--------->[ Resource X ]
        #    |______|______|         |______|______|
        #
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', needs_ports=['n2'], provides_ports=['p1'])
        m.add_resource('Resource X')
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection_to_resource('B', 'n2', 'Resource X')

        # WHEN connection between A:n1 and B:p1 is highlighted
        m.highlight_connection('A', 'n1', 'B', 'p1')

        # THEN this is reflected in the dict representation
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': ['n2'], 'provides_ports': ['p1']}
            ],
            'resources': ['Resource X'],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                    'highlighted': True,
                },
                {
                    'consumer_component': 'B',
                    'consumer_port': 'n2',
                    'resource': 'Resource X',
                },
            ],
        }, m.as_dict())

    def test_InvalidConnection_exception_raised_when_highlighting_unknown_connection(self):
        # GIVEN a mesh with the following component and resource
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |  n2  |--------->[ Resource X ]
        #    |______|______|         |______|______|
        #
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', needs_ports=['n2'], provides_ports=['p1'])
        m.add_resource('Resource X')
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection_to_resource('B', 'n2', 'Resource X')

        # WHEN unknown connection is highlighted
        # THEN an InvalidConnection exception is raised
        self.assertRaises(InvalidConnection, m.highlight_connection, 'Y', 'n1', 'B', 'p1')

    def test_connection_to_resource_can_be_highlighted(self):
        # GIVEN the following mesh
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |  n2  |--------->[ Resource X ]
        #    |______|______|         |______|______|
        #
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', needs_ports=['n2'], provides_ports=['p1'])
        m.add_resource('Resource X')
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection_to_resource('B', 'n2', 'Resource X')

        # WHEN connection to Resource X is highlighted
        m.highlight_connection_to_resource('B', 'n2', 'Resource X')

        # THEN this is reflected in the dict representation
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': ['n2'], 'provides_ports': ['p1']}
            ],
            'resources': ['Resource X'],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
                {
                    'consumer_component': 'B',
                    'consumer_port': 'n2',
                    'resource': 'Resource X',
                    'highlighted': True,
                },
            ],
        }, m.as_dict())

    def test_resource_can_be_highlighted(self):
        # GIVEN the following mesh
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |  n2  |--------->[ Resource X ]
        #    |______|______|         |______|______|
        #
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', needs_ports=['n2'], provides_ports=['p1'])
        m.add_resource('Resource X')
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection_to_resource('B', 'n2', 'Resource X')

        # WHEN Resource X is highlighted
        m.highlight_resource('Resource X')

        # THEN this is reflected in the dict representation
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': ['n2'], 'provides_ports': ['p1']}
            ],
            'resources': ['Resource X'],
            'highlighted_resources': ['Resource X'],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
                {
                    'consumer_component': 'B',
                    'consumer_port': 'n2',
                    'resource': 'Resource X',
                },
            ],
        }, m.as_dict())

    def test_InvalidResource_exception_raised_when_highlighting_unknown_resource(self):
        # GIVEN a mesh with the following component and resource
        #
        #     _____________           _____________
        #    |      A      |         |      B      |
        #    |-------------|         |-------------|
        #    |      |  n1  |-------->|  p1  |  n2  |--------->[ Resource X ]
        #    |______|______|         |______|______|
        #
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1'])
        m.add_component('B', needs_ports=['n2'], provides_ports=['p1'])
        m.add_resource('Resource X')
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection_to_resource('B', 'n2', 'Resource X')

        # WHEN unknown resource is highlighted
        # THEN an InvalidResource exception is raised
        self.assertRaises(InvalidResource, m.highlight_resource, 'Resource K')


class RenderTest(unittest.TestCase):

    JSON_TEMPLATE = '''
        {
            "components" : [
                {% for component in components %}
                {
                    "name": "{{component.name}}",
                    "needs_ports": [{% if component.needs_ports %}
                        "{{ component.needs_ports|join('", "')}}"
                    {% endif %}],
                    "provides_ports": [{% if component.provides_ports %}
                        "{{ component.provides_ports|join('", "')}}"
                    {% endif %}]
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ],

            "resources" : [
                {% if resources %}
                "{{ resources|join('", "') }}"
                {% endif %}
            ],

            "connections": [
                {% for connection in connections %}
                {
                    "consumer_component": "{{ connection.consumer_component }}",
                    "consumer_port": "{{ connection.consumer_port }}",
                    {% if "resource" in connection %}
                    "resource": "{{ connection.resource }}"
                    {% else %}
                    "producer_component": "{{ connection.producer_component }}",
                    "producer_port": "{{ connection.producer_port }}"
                    {% endif %}
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }
    '''

    def test_textual_representation_can_be_rendered_for_an_empty_mesh(self):
        # GIVEN an empty mesh
        m = Mesh()

        # WHEN the textual representation is rendered
        out = render(m, self.JSON_TEMPLATE)

        # THEN the rendered output reflects that of an empty mesh
        out_data = json.loads(out)
        self.assertEqual({'components': [], 'connections': [], 'resources': []}, out_data)

    def test_textual_representation_can_be_rendered_for_a_populated_mesh(self):
        # GIVEN the following mesh
        #
        #     _____________              _____________
        #    |      A      |            |      B      |
        #    |-------------|            |-------------|
        #    |      |  n1  |----------->|  p1  |      |
        #    |      |______|            |______|  nY  |----->[ Resource Y ]
        #    |      |  n2  |-----+  +-->|  p2  |      |
        #    |______|______|     |  |   |______|______|
        #                     +- | -+
        #                     |  |
        #     _____________   |  |      _____________
        #    |      C      |  |  |     |      D      |
        #    |-------------|  |  |     |-------------|
        #    |      |  nX  |--+  +---->|  pX  |  nX  |------>[ Resource X ]
        #    |______|______|           |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1', 'n2'])
        m.add_component('B', provides_ports=['p1', 'p2'], needs_ports=['nY'])
        m.add_component('C', needs_ports=['nX'])
        m.add_component('D', provides_ports=['pX'], needs_ports=['nX'])
        m.add_resource('Resource X')
        m.add_resource('Resource Y')

        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection('A', 'n2', 'D', 'pX')
        m.add_connection('C', 'nX', 'B', 'p2')
        m.add_connection_to_resource('D', 'nX', 'Resource X')
        m.add_connection_to_resource('B', 'nY', 'Resource Y')

        # WHEN the textual representation is rendered
        out = render(m, self.JSON_TEMPLATE)

        # THEN the rendered output reflects that of the mesh
        out_data = json.loads(out)
        self.assertEqual({
            'components': [
                {'name': 'A', 'needs_ports': ['n1', 'n2'], 'provides_ports': []},
                {'name': 'B', 'needs_ports': ['nY'], 'provides_ports': ['p1', 'p2']},
                {'name': 'C', 'needs_ports': ['nX'], 'provides_ports': []},
                {'name': 'D', 'needs_ports': ['nX'], 'provides_ports': ['pX']},
            ],
            'resources': ['Resource X', 'Resource Y'],
            'connections': [
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n1',
                    'producer_component': 'B',
                    'producer_port': 'p1',
                },
                {
                    'consumer_component': 'A',
                    'consumer_port': 'n2',
                    'producer_component': 'D',
                    'producer_port': 'pX',
                },
                {
                    'consumer_component': 'C',
                    'consumer_port': 'nX',
                    'producer_component': 'B',
                    'producer_port': 'p2',
                },
                {
                    'consumer_component': 'D',
                    'consumer_port': 'nX',
                    'resource': 'Resource X',
                },
                {
                    'consumer_component': 'B',
                    'consumer_port': 'nY',
                    'resource': 'Resource Y',
                },
            ],
        }, out_data)

    def test_custom_filters_can_be_injected_into_the_template_renderer(self):
        # GIVEN an arbitrary mesh
        m = Mesh()
        m.add_component('My component')
        m.add_component('Another component')

        # WHEN it is rendered using a custom filter
        template = '{% for c in components %}{{c.name|my_filter}};{% endfor %}'
        filters = {'my_filter': lambda s: s.replace('o', '0')}
        out = render(m, template, custom_filters=filters)

        # THEN the output reflects the rendered mesh with the filtes applied
        self.assertEqual('My c0mp0nent;An0ther c0mp0nent;', out)


class DotRenderTest(unittest.TestCase):

    def test_renderering_the_mesh_as_a_dot_file_to_be_parsed_by_graphviz(self):
        """
        NOTE: This is a very artificial test.

        We've already tested the mesh building and the rendered in the tests above.

        All we're doing here is checking that the DOT template can be parsed an applied. Inspecting the output is
        non trivial and perhaps not worth the while?

        """
        # GIVEN the following mesh
        #
        #     _____________              _____________
        #    |      A      |            |      B      |
        #    |-------------|            |-------------|
        #    |      |  n1  |----------->|  p1  |      |
        #    |      |______|            |______|      |
        #    |      |  n2  |-----+  +-->|  p2  |      |
        #    |______|______|     |  |   |______|______|
        #                     +- | -+
        #                     |  |
        #     _____________   |  |      _____________
        #    |      C      |  |  |     |      D      |
        #    |-------------|  |  |     |-------------|
        #    |      |  nX  |--+  +---->|  pX  |      |
        #    |______|______|           |______|______|
        #
        m = Mesh()
        m.add_component('A', needs_ports=['n1', 'n2'])
        m.add_component('B', provides_ports=['p1', 'p2'])
        m.add_component('C', needs_ports=['nX'])
        m.add_component('D', provides_ports=['pX'])

        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection('A', 'n2', 'D', 'pX')
        m.add_connection('C', 'nX', 'B', 'p2')

        # WHEN the dot representation is rendered
        # THEN the world does not come to an end ("WHAT??" you say? See docstring above)
        render_mesh_as_dot(m)


if __name__ == '__main__':
    unittest.main()
