import os
import xmltodict
import json
import package_manager
import nuget_api_manager
from pyvis.network import Network


def initialize_pyvis_network():
    net = Network(
        height="1080",
        width="1920",
        bgcolor="#fbfbfb",
        font_color="black",
        select_menu=True,
        directed=True,
        filter_menu=True,
    )
    net.set_options(
        """
    const options = {
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true
                }
            },
            "smooth": false
        },
        "layout": {
            "hierarchical": {
                "enabled": true,
                "levelSeparation": 250,
                "nodeSpacing": 350,
                "treeSpacing": 650,
                "edgeMinimization": true,
                "sortMethod": "directed",
                "parentCentralization": true
            }
        },
        "interaction": {
            "hover": true
        },
        "manipulation": {
            "enabled": true
        },
        "physics": {
            "enabled": false,
            "hierarchicalRepulsion": {
                "nodeDistance": 150,
                "avoidOverlap": 1
            },
            "solver": "hierarchicalRepulsion"
        }
    }"""
    )
    return net


def generate_csproj_basic_graph(csproj_data):
    print(f"Generating Basic Graph for {csproj_data.Name} project")
    net = initialize_pyvis_network()

    net.add_node(csproj_data.Name, label=csproj_data.Name, color="#88d184", level=0)

    # add the project dependencies
    package_references = csproj_data.ProjectReferences
    if len(package_references) > 0:
        for package in package_references:
            net.add_node(package, label=package, color="#88d184", level=1)
            # net.add_edge(csproj_data.Name, to=package)
            net.add_edge(package, to=csproj_data.Name)

    # add the nuget dependencies

    nuget_dependencies = csproj_data.NuGetDependencies[csproj_data.Framework]
    for dependency in nuget_dependencies:
        net.add_node(
            dependency.PackageName + "_" + dependency.VersionRange.Base,
            label=dependency.PackageName + " : " + dependency.VersionRange.Base,
            color="#2383ce",
            level=2,
        )

        # net.add_edge(csproj_data.Name, to=dependency.PackageName + "_" + dependency.VersionRange.Base)
        net.add_edge(
            dependency.PackageName + "_" + dependency.VersionRange.Base,
            to=csproj_data.Name,
        )

    print(net.get_nodes())
    print(net.get_edges())

    net.show(csproj_data.Name + "_basic_dependency_graph.html")


def generate_soln_basic_graph(solution_file_name, csproj_package_mapper):

    print(f"Generating Basic Graph for {solution_file_name} solution")
    net = initialize_pyvis_network()

    net.add_node(
        solution_file_name + "_sln", label=solution_file_name, color="#bd8bf3", level=0
    )

    for csproj_name in csproj_package_mapper:
        net.add_node(csproj_name, label=csproj_name, color="#88d184", level=1)
        net.add_edge(solution_file_name + "_sln", to=csproj_name)

    # add the project dependencies
    for csproj_name in csproj_package_mapper:
        package_references = csproj_package_mapper[csproj_name].ProjectReferences
        if len(package_references) > 0:
            for package in package_references:
                # net.add_edge(csproj_name, to=package)
                net.add_edge(package, to=csproj_name)

    # add the nuget dependencies
    for csproj_name in csproj_package_mapper:
        pkg = csproj_package_mapper[csproj_name]
        nuget_dependencies = pkg.NuGetDependencies[pkg.Framework]
        for dependency in nuget_dependencies:
            net.add_node(
                dependency.PackageName + "_" + dependency.VersionRange.Base,
                label=dependency.PackageName + " : " + dependency.VersionRange.Base,
                color="#2383ce",
                level=2,
            )
            package_label = ""
            if pkg.DataType == "nuget":
                package_label = pkg.Name + "_" + pkg.Version
            elif pkg.DataType == "csproj":
                package_label = pkg.Name
            # net.add_edge(package_label, to=dependency.PackageName + "_" + dependency.VersionRange.Base)
            net.add_edge(
                dependency.PackageName + "_" + dependency.VersionRange.Base,
                to=package_label,
            )

    print(net.get_nodes())
    print(net.get_edges())

    net.show(solution_file_name + "_basic_dependency_graph.html")


def generate_soln_deep_graph(solution_file_name, csproj_package_mapper, sub_packages):
    print(f"Generating Deep Graph for {solution_file_name} solution")
    net = initialize_pyvis_network()

    net.add_node(
        solution_file_name + "_sln", label=solution_file_name, color="#bd8bf3", level=0
    )

    for csproj_name in csproj_package_mapper:
        net.add_node(csproj_name, label=csproj_name, color="#88d184", level=1)
        net.add_edge(solution_file_name + "_sln", to=csproj_name)

    # add the project dependencies
    for csproj_name in csproj_package_mapper:
        pkg = csproj_package_mapper[csproj_name]
        net = generate_csproj_deep_net(net, pkg, sub_packages)

    print(net.get_nodes())
    print(net.get_edges())

    net.show(solution_file_name + "_deep_dependency_graph.html")


def generate_csproj_deep_graph(csproj_package, sub_packages):
    net = initialize_pyvis_network()
    net = generate_csproj_deep_net(net, csproj_package, sub_packages)
    print(net.get_nodes())
    print(net.get_edges())
    net.show(csproj_package.Name + "_deep_dependency_graph.html")


def generate_csproj_deep_net(net, csproj_package, sub_packages):

    print(f"Generating Deep Graph for {csproj_package.Name} project")

    net.add_node(
        csproj_package.Name, label=csproj_package.Name, color="#88d184", level=0
    )

    # add the project dependencies
    package_references = csproj_package.ProjectReferences
    if len(package_references) > 0:
        for package in package_references:
            net.add_node(package, label=package, color="#88d184", level=1)
            # net.add_edge(csproj_data.Name, to=package)
            net.add_edge(package, to=csproj_package.Name)
            net.add_edge(package, to=csproj_package.Name)

    # add the nuget dependencies
    def pd(pkg, sub_pkg, lvl):
        # iterate over the keys. There will be just one key here
        print(pkg.Name + " " + pkg.Framework)
        if pkg.Framework != "":
            nuget_dependencies = pkg.NuGetDependencies[pkg.Framework]
            for dependency in nuget_dependencies:
                net.add_node(
                    dependency.PackageName + "_" + dependency.VersionRange.Base,
                    label=dependency.PackageName + " : " + dependency.VersionRange.Base,
                    level=lvl,
                )

                if pkg.DataType == "nuget":
                    package_label = pkg.Name + "_" + pkg.Version
                elif pkg.DataType == "csproj":
                    package_label = pkg.Name
                # net.add_edge(package_label, to=dependency.PackageName + "_" + dependency.VersionRange.Base)
                net.add_edge(
                    dependency.PackageName + "_" + dependency.VersionRange.Base,
                    to=package_label,
                )
                if (
                    dependency.PackageName + "_" + dependency.VersionRange.Base
                ) in sub_packages:
                    pd(
                        sub_packages[
                            dependency.PackageName + "_" + dependency.VersionRange.Base
                        ],
                        sub_pkg,
                        lvl + 1,
                    )

    pd(csproj_package, sub_packages, 2)

    return net


def search_and_auto_generate_data(query, version):
    package_data = nuget_api_manager.search_and_auto_generate_data(query)
    pkg_manager = package_manager.PackageManager("NuGet")
    pkg_manager.initialize_from_nuget_data(package_data)
    generate_catalog_data(pkg_manager, version)
    return pkg_manager


def print_csproj_dependency(master_package, sub_packages, target_framework):
    def pd(pkg, sub_pkg, fw, print_indent):
        tabs = "\t" * print_indent
        if target_framework not in pkg.NuGetDependencies:
            # print(tabs + "N/A")
            return
        for dependency in pkg.NuGetDependencies[target_framework]:
            print(tabs + dependency.PackageName + " : " + dependency.VersionRange.Base)
            pd(sub_packages[dependency.PackageName], sub_pkg, fw, print_indent + 1)

    print("Printing Dependency Tree ")
    print(master_package.Name + " : " + master_package.Version)
    pd(master_package, sub_packages, target_framework, 1)


def read_and_retrieve_csproj_data(solution_file, solution_path):
    last_index = solution_path.rfind("\\")
    solution_dir = solution_path[:last_index]
    csproj_map = {}

    for line in solution_file.readlines():
        if 'Project("{' in line:
            # hacking the code for now using spilt and replace
            line = line.split("=")
            # first would be the project and its identifier and second would contain string with ,
            second = line[1]
            second = second.split(",")

            csproj = second[0].replace('"', "")
            csproj = csproj.replace(" ", "")
            csproj_path = second[1].replace('"', "")
            csproj_path = csproj_path.replace(" ", "")

            if ".csproj" in csproj_path:
                csproj_map[csproj] = os.path.join(solution_dir, csproj_path)

    return csproj_map


def read_and_deserialize_solution(soln_path):

    soln_file = open(soln_path, "r")
    csproj_map = read_and_retrieve_csproj_data(soln_file, soln_path)
    soln_file.close()
    return csproj_map


def generate_for_solution():
    soln_path = ""
    while True:
        choice = input("Enter the full path of solution: ")
        if not os.path.exists(choice):
            print(choice + " not found")
        else:
            soln_path = choice
            break
    csproj_path_mapper = read_and_deserialize_solution(soln_path)
    last_index = soln_path.rfind("\\")
    solution_file_name = soln_path[last_index + 1 :]
    solution_file_name = solution_file_name.replace(".sln", "")

    # read all the csproj and put in map
    csproj_package_mapper = {}
    for csproj_name in csproj_path_mapper:
        print("Reading " + csproj_name)
        csproj_package_mapper[csproj_name] = read_and_deserialize_csproj(
            csproj_path_mapper[csproj_name]
        )

    print("What would you like to do next:")
    while True:
        choice = input(
            "1. Generate Package/NuGet Reference Graph for solution\n2. Generate Deep Graph\n3. Return to previous menu: "
        )
        if choice == "1":
            # generate the basic graph
            generate_soln_basic_graph(solution_file_name, csproj_package_mapper)

        elif choice == "2":
            # call the function:
            # should take package list
            # or should take whole as argument
            # need to refactor
            sub_packages = {}
            for csproj_name in csproj_path_mapper:
                generate_nuget_dependency_for_csproj(
                    csproj_package_mapper[csproj_name], sub_packages
                )

            generate_soln_deep_graph(
                solution_file_name, csproj_package_mapper, sub_packages
            )

        elif choice == "3":
            return
        else:
            print("Invalid Choice. Try Again!")


def read_and_deserialize_csproj(csproj_path):
    csproj_file = open(csproj_path, "rb")
    ordered_data_dict = xmltodict.parse(csproj_file)
    csproj_file.close()
    csproj_data = json.loads(json.dumps(ordered_data_dict))

    csproj = package_manager.PackageManager(data_type="csproj")
    csproj.initialize_from_csproj(csproj_data)

    if csproj.Name is None or csproj.Name == "":
        # get name from path
        dirs = csproj_path.split("\\")
        csproj.Name = dirs[-1].replace(".csproj", "")

    return csproj


def generate_catalog_data(pkg_mgr, version):
    if version == "":
        version = pkg_mgr.LatestVersion

    # set the version here
    pkg_mgr.set_package_version(version)

    # get the catalog data for the version
    catalog_data = nuget_api_manager.get_catalog_entry_by_version_url(
        pkg_mgr.PackageVersionURL
    )

    if catalog_data is None:
        return "Invalid catalog data"

    pkg_mgr.set_catalog_data_json(catalog_data)


def generate_nuget_dependency_for_csproj(csproj_data, sub_packages):

    if len(csproj_data.SupportedFrameworks) > 1:
        # if more than one framework exists
        print(
            "Choose framework to generate dependency. Please enter the serial number:"
        )
        csproj_data.print_available_frameworks_with_index()
        while True:
            choice = input("Enter your choice: ")
            if not choice.isnumeric():
                print("Please enter the serial number!")
            elif 1 <= int(choice) <= len(csproj_data.SupportedFrameworks):
                csproj_data.Framework = csproj_data.SupportedFrameworks[int(choice) - 1]
                print(csproj_data.Framework + " framework selected")
                break
            else:
                print("Invalid Choice!")

    visited_packages = {}
    package_stack = []

    # add the NuGet dependencies in stack
    package_stack.extend(csproj_data.NuGetDependencies[csproj_data.Framework])

    # generate dependencies:
    while package_stack:

        temp_package_list = []
        while package_stack:

            package = package_stack.pop(0)
            if (
                package.PackageName + "_" + package.VersionRange.Base
            ) not in sub_packages:

                # search for package in nuget
                sub_package_data = nuget_api_manager.search_and_auto_generate_data(
                    package.PackageName, package.VersionRange.Base
                )
                # refactor it
                sub_pkg_mgr = package_manager.PackageManager("NuGet")
                sub_pkg_mgr.initialize_from_nuget_data(sub_package_data)
                # generate the catalog data
                generate_catalog_data(sub_pkg_mgr, package.VersionRange.Base)
                # add the name and version to the dictionary
                # key:
                # name_version
                sub_packages[sub_pkg_mgr.Name + "_" + sub_pkg_mgr.Version] = sub_pkg_mgr
                # get the dependencies and add to a list
                # TODO need a mechanism to decode target framework
                # TODO csproj has FW in another ways and we need to translate it to supported versions. Need decoding logic

                for dg in sub_pkg_mgr.NuGetDependencies:
                    if str.lower(csproj_data.Framework) == str.lower(dg):
                        sub_pkg_mgr.Framework = dg
                        for dependency in sub_pkg_mgr.NuGetDependencies[dg]:
                            if dependency.PackageName not in visited_packages:
                                temp_package_list.append(dependency)

        package_stack.extend(temp_package_list)


def generate_for_csproj():
    csproj_path = ""
    while True:
        choice = input("Enter the csproj path: ")
        if not os.path.exists(choice):
            print(choice + " not found")
        else:
            csproj_path = choice
            break
    csproj_data = read_and_deserialize_csproj(csproj_path)

    print("What would you like to do: ")
    while True:
        choice = input(
            "1. Display Package Details\n2. Generate Dependency Tree\n3. Return to Main Menu: "
        )
        if choice == "1":
            csproj_data.print_package_data()

        elif choice == "2":

            sub_choice = ""

            while True:

                sub_choice = input(
                    "1. Generate Package/NuGet Reference Graph for project\n2. Generate Deep Graph\n3. Return to previous menu:"
                )

                if sub_choice == "1":
                    # generate the basic graph
                    generate_csproj_basic_graph(csproj_data)

                elif sub_choice == "2":

                    sub_packages = {}
                    generate_nuget_dependency_for_csproj(csproj_data, sub_packages)
                    # framework_from_nuget = ""
                    # print_csproj_dependency(csproj_data, sub_packages, framework_from_nuget)
                    generate_csproj_deep_graph(csproj_data, sub_packages)

                elif sub_choice == "3":
                    break

        elif choice == "3":
            return
        else:
            print("Invalid Choice. Please enter the correct choice:")
            continue


def options():
    print("Generate for:")
    while True:
        choice = input("1. Solution\n2. csproj\n3. Return to previous menu: ")
        if choice == "1":
            generate_for_solution()
            return
        elif choice == "2":
            generate_for_csproj()
        elif choice == "3":
            return
        else:
            print("Invalid Choice. Try again!")
