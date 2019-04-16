import hexaviz

def main():
    m = hexaviz.Mesh()

    m.add_component('service1', needs_ports=['n1', 'n2'], provides_ports=['p1'])

    m.add_component('service2', needs_ports=['n1', 'n2'], provides_ports=['p2'])
    m.add_component('service3', needs_ports=['n13', 'n23'], provides_ports=['p13', 'p23'])
    m.add_component('service4', needs_ports=['n14'], provides_ports=['p14', 'p24'])

    m.add_domain('MyDomain')
    m.add_component_to_domain('service1', 'MyDomain')
    m.add_component_to_domain('service2', 'MyDomain')

    m.expose_component_provides_port('service1', 'p1')
    m.expose_component_provides_port('service2', 'p2')
    m.expose_component_needs_port('service2', 'n2')
    m.expose_component_needs_port('service1', 'n2')

    m.add_connection('service1', 'n1', 'service2', 'p2')
    m.add_connection('MyDomain', 'n2', 'service3', 'p23')
    m.add_connection('service4', 'n14', 'MyDomain', 'p1')
    print hexaviz.render_mesh_as_dot(m)


if __name__ == '__main__':
    main()
