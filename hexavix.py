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
"""
Example usage:

        m = Mesh()

        m.add_component('A', needs_ports=['n1', 'n2'])
        m.add_component('B', provides_ports=['p1', 'p2'])
        m.add_component('C', needs_ports=['nX'])
        m.add_component('D', provides_ports=['pX'])

        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection('A', 'n2', 'D', 'pX')
        m.add_connection('C', 'nX', 'B', 'p2')

        print render_mesh_as_dot(m)


The output can then be visualised using Graphviz dot to produce and output that akin to:
            _____________              _____________
           |      A      |            |      B      |
           |-------------|            |-------------|
           |      |  n1  |----------->|  p1  |      |
           |      |______|            |______|      |
           |      |  n2  |-----+  +-->|  p2  |      |
           |______|______|     |  |   |______|______|
                            +- | -+
                            |  |
            _____________   |  |      _____________
           |      C      |  |  |     |      D      |
           |-------------|  |  |     |-------------|
           |      |  nX  |--+  +---->|  pX  |      |
           |______|______|           |______|______|

"""
import re
import hashlib
import textwrap
from collections import OrderedDict

from jinja2 import Environment


class DuplicateEntry(Exception):
    """Raised when a duplicate element is added to the mesh.
    """


class InvalidComponent(Exception):
    """Raised when a referencing a component that does not exist in the mesh.
    """


class InvalidPort(Exception):
    """Raised when a referencing an invalid port on a component in the mesh.
    """


class InvalidConnection(Exception):
    """Raised when there is an attempt to create an invalid connection in the mesh.
    """


class Mesh(object):
    """Light-weight representation of a hexagonal mesh that can drive template renderers (e.g. jinja2) to
    produce a textual representation of the mesh.
    """

    GRAPH_TEMPLATE = ''

    def __init__(self):
        self.components = OrderedDict()
        self.connections = []
        self.connected_consumers = set()

    def add_component(self, component_name, needs_ports=None, provides_ports=None):
        """Adds a component to the mesh.

        :param str component_name: Name of component to add
        :param list needs_port: List of needs ports for this component
        :param list provides_ports: List of provides ports for this component
        :raises: DuplicateEntry if component of that name already exists
        """
        if component_name in self.components:
            raise DuplicateEntry('Component with name {0} already exists'.format(component_name))

        self.components[component_name] = ComponentNode(component_name)

        needs = needs_ports or tuple()
        for port_name in needs:
            self.add_needs_port(component_name, port_name)

        provides = provides_ports or tuple()
        for port_name in provides:
            self.add_provides_port(component_name, port_name)

    def add_needs_port(self, component_name, port_name):
        """Assigns an additional needs port to an existing component.

        :param str component_name: name of component to add the port to
        :param str port_name: name of needs port to add
        :raises: DuplicateEntry if that needs port already exists on the component
        """
        self.components[component_name].add_needs_port(port_name)

    def add_provides_port(self, component_name, port_name):
        """Assigns an additional provides port to an existing component.

        :param str component_name: name of component to add the port to
        :param str port_name: name of provides port to add
        :raises: DuplicateEntry if that provides port already exists on the component
        """
        self.components[component_name].add_provides_port(port_name)

    def add_connection(self, consumer_component, consumer_port, producer_component, producer_port):
        """Adds a connection between a needs port from a consumer component to the provides port of a producer.

        :param str consumer_component: name of the consumer component
        :param str consumer_port: name of the needs port of the consumer
        :param str producer_component: name of the producer component
        :param str producer_port: name of the provides port of the producer
        """
        try:
            self.components[consumer_component].assert_is_valid_needs_port(consumer_port)
        except KeyError:
            raise InvalidComponent('{0} component does not exist in the mesh'.format(consumer_component))

        try:
            self.components[producer_component].assert_is_valid_provides_port(producer_port)
        except KeyError:
            raise InvalidComponent('{0} component does not exist in the mesh'.format(producer_component))

        consumer = consumer_component, consumer_port
        producer = producer_component, producer_port

        if consumer in self.connected_consumers:
            raise InvalidConnection('{0} already connected'.format(consumer))

        self.connections.append(ConnectionNode(consumer, producer))
        self.connected_consumers.add(consumer)

    def as_dict(self):
        """Returns a dict representation of the mesh.
        """
        return {
            'components': [c.as_dict() for c in self.components.values()],
            'connections': [c.as_dict() for c in self.connections],
        }


class ConnectionNode(object):
    """Internal representation of a connection within the mesh.
    """
    def __init__(self, consumer, producer):
        """Instantiates a new connection between the given consumer and producer.

        :param tuple consumer: consumer of the connection defined as (consumer_component, consumer_port)
        :param tuple producer: producer of the connection defined as (producer_component, producerport)
        """
        self.consumer_component, self.consumer_port = consumer
        self.producer_component, self.producer_port = producer

    def as_dict(self):
        """Returns a dict representation of the component.
        """
        return {
            'consumer_component': self.consumer_component,
            'consumer_port': self.consumer_port,
            'producer_component': self.producer_component,
            'producer_port': self.producer_port,
        }


class ComponentNode(object):
    """Internal representation of a Component within the mesh.
    """

    def __init__(self, name):
        """Instantiates the component node with a given name

        :param str name: component name
        """
        self.name = name
        self.needs_ports = []
        self.provides_ports = []

    def add_needs_port(self, port_name):
        """Assigns a needs port.

        :param str port_name: name of needs port to add
        :raises: DuplicateEntry if that needs port already exists
        """
        if port_name in self.needs_ports:
            raise DuplicateEntry('Needs port with name {0} already exists for {1}'.format(port_name, self.name))

        self.needs_ports.append(port_name)

    def add_provides_port(self, port_name):
        """Assigns a provides port.

        :param str port_name: name of provides port to add
        :raises: DuplicateEntry if that provides port already exists
        """
        if port_name in self.provides_ports:
            raise DuplicateEntry('Provides port with name {0} already exists for {1}'.format(port_name, self.name))

        self.provides_ports.append(port_name)

    def as_dict(self):
        """Returns a dict representation of the component.
        """
        return {
            'name': self.name,
            'needs_ports': list(self.needs_ports),
            'provides_ports': list(self.provides_ports),
        }

    def assert_is_valid_needs_port(self, port_name):
        """Raises InvalidPort if given port is not a valid needs port.
        """
        if port_name not in self.needs_ports:
            raise InvalidPort('{0} is not a valid valid needs port for component {1}'.format(port_name, self.name))

    def assert_is_valid_provides_port(self, port_name):
        """Raises InvalidPort if given port is not a valid provides port.
        """
        if port_name not in self.provides_ports:
            raise InvalidPort('{0} is not a valid valid provides port for component {1}'.format(port_name, self.name))


def render(mesh, template, custom_filters=None):
    """Renders the given mesh using the template text provided.

    The template and filters should be compatible with jinja2

    :param str template: the template text to be used for rendering
    :param dict custom_filters: dict of custom filters where the key is the filter tag and the value is the callables
    :returns: rendered textual representation of the mesh
    """
    jinja_env = Environment()
    if custom_filters:
        jinja_env.filters.update(custom_filters)

    jinja_template = jinja_env.from_string(template)

    return jinja_template.render(mesh.as_dict())


def render_mesh_as_dot(mesh):
    """Renders the given mesh in the Graphviz dot format.

    :param Mesh mesh: the mesh to be rendered
    :returns: textual dot representation of the mesh
    """

    custom_filters = {
        'hash': lambda s: "id" + hashlib.md5(s).hexdigest()[:6],
        'escape': lambda s: re.sub(r'([{}|"<>])', r'\\\1', s),
    }

    template = textwrap.dedent('''
        digraph G {

            rankdir=LR;
            node [shape=record];

            {% for component in components %}
            {{ component.name|hash }} [label="{{ component.name|escape }} | {
                {
                    {% for port in component.provides_ports %}
                    <{{ port|hash }}>{{ port|escape }}{% if not loop.last %}|{% endif %}
                    {% endfor %}
                }|{
                    {% for port in component.needs_ports %}
                    <{{ port|hash }}>{{ port|escape }}{% if not loop.last %}|{% endif %}
                    {% endfor %}
                }
            }"];
            {% endfor %}

            {% for conn in connections %}
            {{ conn.consumer_component|hash }}:{{ conn.consumer_port|hash }} -> {{ conn.producer_component|hash }}:{{ conn.producer_port|hash }};
            {% endfor %}
        }
    ''').lstrip()

    return render(mesh, template, custom_filters=custom_filters)
