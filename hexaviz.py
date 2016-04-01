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

        # Crete a mesh (collection of connected components)
        m = Mesh()

        # Add components (hexagons) to the mesh, each with a set of 'needs' ports (output ports) and
        # and 'provides' ports (input ports)
        m.add_component('A', needs_ports=['n1', 'n2'])
        m.add_component('B', provides_ports=['p1', 'p2'])
        m.add_component('C', needs_ports=['nX'])
        m.add_component('D', needs_ports=['data'], provides_ports=['pX'])

        # Add pass-through adapters to connect ports between components
        m.add_connection('A', 'n1', 'B', 'p1')
        m.add_connection('A', 'n2', 'D', 'pX')
        m.add_connection('C', 'nX', 'B', 'p2')

        # Define an external adapter and attach it to a 'needs' port
        m.add_resource('Resource X')
        m.add_connection_to_resource('D', 'data', 'Resource X')

        # Render as a Graphviz dot file
        print render_mesh_as_dot(m)


When visualised using Graphviz, this should produce an output that looks like:

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
           |      |  nX  |--+  +---->|  pX  | data |------->[  Resource X  ]
           |______|______|           |______|______|

"""
import re
import hashlib
import textwrap
from jinja2 import Environment
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


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


class InvalidResource(Exception):
    """Raised when there is an attempt to create an invalid resource in the mesh.
    """


class Mesh(object):
    """Light-weight representation of a hexagonal mesh that can drive template renderers (e.g. jinja2) to
    produce a textual representation of the mesh.
    """

    GRAPH_TEMPLATE = ''

    def __init__(self):
        self.components = OrderedDict()
        self.connections = OrderedDict()
        self.resources = []
        self._highlighted_resource = set()
        self.connected_consumers = set()

    def add_component(self, component_name, needs_ports=None, provides_ports=None):
        """Adds a component to the mesh.

        :param str component_name: Name of component to add
        :param list needs_ports: List of needs ports for this component
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

    def add_resource(self, resource_name):
        """Adds a resource (adapter to external data) to the mesh.

        :param str resource_name: Name of resource to add
        :raises: DuplicateEntry if component of that name already exists
        """
        if resource_name in self.resources:
            raise DuplicateEntry('Resource with name {0} already exists'.format(resource_name))

        self.resources.append(resource_name)

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

        self.connections[consumer, producer] = (ConnectionNode(consumer, producer))
        self.connected_consumers.add(consumer)

    def add_connection_to_resource(self, consumer_component, consumer_port, resource):
        """Adds a connection between a needs port from a consumer component to a resource.

        :param str consumer_component: name of the consumer component
        :param str consumer_port: name of the needs port of the consumer
        :param str resource: name of resource
        """
        try:
            self.components[consumer_component].assert_is_valid_needs_port(consumer_port)
        except KeyError:
            raise InvalidComponent('{0} component does not exist in the mesh'.format(consumer_component))

        if resource not in self.resources:
            raise InvalidResource('{0} resource does not exist in the mesh'.format(resource))

        consumer = consumer_component, consumer_port
        connection = ResourceConnectionNode(consumer, resource)

        if consumer in self.connected_consumers:
            raise InvalidConnection('{0} already connected'.format(consumer))

        self.connections[consumer, resource] = connection
        self.connected_consumers.add(consumer)

    def highlight_component(self, component_name):
        """Highlights a component in the mesh.

        :param str component_name: name of component to highlight
        """
        try:
            self.components[component_name].highlighted = True
        except KeyError:
            raise InvalidComponent('{0} component does not exist in the mesh'.format(component_name))

    def highlight_connection(self, consumer_component, consumer_port, producer_component, producer_port):
        """Highlights a connection between a needs port from a consumer component to the provides port of a producer.

        :param str consumer_component: name of the consumer component
        :param str consumer_port: name of the needs port of the consumer
        :param str producer_component: name of the producer component
        :param str producer_port: name of the provides port of the producer
        """
        consumer = consumer_component, consumer_port
        producer = producer_component, producer_port
        try:
            self.connections[consumer, producer].highlighted = True
        except KeyError:
            raise InvalidConnection('Invalid Connection: {0} -> {1}'.format(consumer, producer))

    def highlight_connection_to_resource(self, consumer_component, consumer_port, resource):
        """Highlights a connection between a needs port and a resource.

        :param str consumer_component: name of the consumer component
        :param str consumer_port: name of the needs port of the consumer
        :param str resource: name of resource
        """
        consumer = consumer_component, consumer_port
        try:
            self.connections[consumer, resource].highlighted = True
        except KeyError:
            raise InvalidConnection('Invalid Connection: {0} -> {1}'.format(consumer, resource))

    def highlight_resource(self, resource):
        """Highlights a resource in the mesh.

        :param str resource: name of resource to highlight
        """
        if resource not in self.resources:
            raise InvalidResource('{0} resource does not exist in the mesh'.format(resource))

        self._highlighted_resource.add(resource)

    def as_dict(self):
        """Returns a dict representation of the mesh.
        """
        d = {
            'components': [c.as_dict() for c in self.components.values()],
            'connections': [c.as_dict() for c in self.connections.values()],
            'resources': [r for r in self.resources],
        }

        if self._highlighted_resource:
            d['highlighted_resources'] = list(self._highlighted_resource)

        return d


class ConnectionNode(object):
    """Internal representation of a connection between components within the mesh.
    """
    def __init__(self, consumer, producer):
        """Instantiates a new connection between the given consumer and producer.

        :param tuple consumer: consumer of the connection defined as (consumer_component, consumer_port)
        :param tuple producer: producer of the connection defined as (producer_component, producer_port)
        """
        self.consumer = consumer
        self.producer = producer
        self.highlighted = False

    def as_dict(self):
        """Returns a dict representation of the connection.
        """
        self.consumer_component, self.consumer_port = self.consumer
        self.producer_component, self.producer_port = self.producer
        d = {
            'consumer_component': self.consumer_component,
            'consumer_port': self.consumer_port,
            'producer_component': self.producer_component,
            'producer_port': self.producer_port,
        }

        if self.highlighted:
            d['highlighted'] = True

        return d


class ResourceConnectionNode(ConnectionNode):
    """Internal representation of a connection between components and resources within the mesh.
    """
    def as_dict(self):
        """Returns a dict representation of the connection.
        """
        self.consumer_component, self.consumer_port = self.consumer
        d = {
            'consumer_component': self.consumer_component,
            'consumer_port': self.consumer_port,
            'resource': self.producer,
        }

        if self.highlighted:
            d['highlighted'] = True

        return d


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
        self.highlighted = False

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
        d = {
            'name': self.name,
            'needs_ports': list(self.needs_ports),
            'provides_ports': list(self.provides_ports),
        }

        if self.highlighted:
            d['highlighted'] = True

        return d

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
        # alternative hash for provides ports to avoid conflicts with needs ports with same name
        'hash_p': lambda s: "idp" + hashlib.md5(s).hexdigest()[:6],
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
                    <{{ port|hash_p }}>{{ port|escape }}{% if not loop.last %}|{% endif %}
                    {% endfor %}
                }|{
                    {% for port in component.needs_ports %}
                    <{{ port|hash }}>{{ port|escape }}{% if not loop.last %}|{% endif %}
                    {% endfor %}
                }
            }"{% if component.highlighted %}, color="red"{% endif %}];
            {% endfor %}

            {% for resource in resources %}
            {{ resource|hash }} [label="{{ resource }}", style="dashed"{% if resource in highlighted_resources %}, color="red"{% endif %}];
            {% endfor %}

            {% for conn in connections %}
            {% if "resource" in conn %}
            {{ conn.consumer_component|hash }}:{{ conn.consumer_port|hash }} -> {{ conn.resource|hash }} [style="dashed"{% if conn.highlighted %}, color="red"{% endif %}];
            {% else %}
            {{ conn.consumer_component|hash }}:{{ conn.consumer_port|hash }} -> {{ conn.producer_component|hash }}:{{ conn.producer_port|hash_p }}{% if conn.highlighted %}[color="red"]{% endif %};
            {% endif %}
            {% endfor %}
        }
    ''').lstrip()

    return render(mesh, template, custom_filters=custom_filters)
