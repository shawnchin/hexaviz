import hexaviz

def main():
    m = hexaviz.Mesh()

    m.add_component('service1', needs_ports=['n1', 'n2'], provides_ports=['p1', 'p2'])

    m.add_component('service2', needs_ports=['n12', 'n22'], provides_ports=['p12', 'p22'])
    m.add_component('service3', needs_ports=['n13', 'n23'], provides_ports=['p13', 'p23'])
    m.add_component('service4', needs_ports=['n14', 'n24'], provides_ports=['p14', 'p24'])

    m.add_domain('MyDomain', needs_ports=['n2', 'n23'], provides_ports=['p1', 'p2', 'p12'])
    m.add_component_to_domain('service1', 'MyDomain')
    m.add_component_to_domain('service2', 'MyDomain')
    #m.expose_component_provides_port('service1', 'p1')
    #from pprint import pprint
    #pprint(m.as_dict())
    print hexaviz.render_mesh_as_dot(m)


if __name__ == '__main__':
    main()