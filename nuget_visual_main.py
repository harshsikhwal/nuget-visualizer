import nuget_api_manager
import package_manager
from pyvis.network import Network
import solution_manager

# add binder


def generate_dependency_graph(master_package, sub_packages, target_framework):
    net = Network(
        height="1080",
        width="1920",
        bgcolor="#fbfbfb",
        font_color="black",
        select_menu=True,
        directed=True,
        filter_menu=True,
    )

    def pd(pkg, sub_pkg, fw):
        if target_framework not in pkg.NuGetDependencies:
            # net.add_node("N/A")
            # net.add_edge(pkg.Name, "N/A")
            return
        for dependency in pkg.NuGetDependencies[target_framework]:
            # TODO for similar nodes, put same colour
            net.add_node(
                dependency.PackageName,
                label=dependency.PackageName + " : " + dependency.VersionRange.Base,
            )
            net.add_edge(pkg.Name, dependency.PackageName)
            pd(sub_packages[dependency.PackageName], sub_pkg, fw)

    print("Generating graph")
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
    net.add_node(
        master_package.Name, label=master_package.Name + " : " + master_package.Version
    )
    pd(master_package, sub_packages, target_framework)
    net.show(
        master_package.Name + "_" + master_package.Version + "_dependency_graph.html"
    )


def search_and_auto_generate_data(query, version):
    package_data = nuget_api_manager.search_and_auto_generate_data(query)
    pkg_manager = package_manager.PackageManager("NuGet")
    pkg_manager.initialize_from_nuget_data(package_data)
    generate_catalog_data(pkg_manager, version)
    return pkg_manager


def print_dependency(master_package, sub_packages, target_framework):
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


def generate_dependency_data(master_package):
    print("Choose framework to generate dependency. Please enter the serial number:")
    master_package.print_available_frameworks_with_index()
    target_framework = ""
    while True:
        choice = input("Enter your choice: ")
        if not choice.isnumeric():
            print("Please enter the serial number!")
            pass
        elif 1 <= int(choice) <= len(master_package.SupportedFrameworks):
            target_framework = master_package.SupportedFrameworks[int(choice) - 1]
            print(target_framework + " framework selected")
            break
        else:
            print("Invalid Choice!")

    sub_packages = {}
    visited_packages = {}
    package_stack = []
    package_stack.extend(master_package.NuGetDependencies[target_framework])
    # generate dependencies:
    while package_stack:

        temp_package_list = []
        while package_stack:

            package = package_stack.pop(0)
            if package.PackageName in visited_packages:
                pass
            else:
                # search for package in nuget
                sub_package_data = nuget_api_manager.search_and_auto_generate_data(
                    package.PackageName, package.VersionRange.Base
                )
                # refactor it
                sub_pkg_mgr = package_manager.PackageManager("NuGet")
                sub_pkg_mgr.initialize_from_nuget_data(sub_package_data)
                # generate the catalog data
                generate_catalog_data(sub_pkg_mgr, package.VersionRange.Base)
                # add to the dictionary
                sub_packages[sub_pkg_mgr.Name] = sub_pkg_mgr
                # get the dependencies and add to a list
                if target_framework in sub_pkg_mgr.NuGetDependencies:
                    for dependency in sub_pkg_mgr.NuGetDependencies[target_framework]:
                        if dependency.PackageName not in visited_packages:
                            temp_package_list.append(dependency)
                # add to visited
                visited_packages[sub_pkg_mgr.Name] = True
        package_stack.extend(temp_package_list)

    print_dependency(master_package, sub_packages, target_framework)
    generate_dependency_graph(master_package, sub_packages, target_framework)


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


def search():
    package_name = input("Enter the package name: ")
    if package_name == "" or package_name is None:
        print("Invalid package name!")
        return
    master_package_data = nuget_api_manager.search_by_title(package_name)

    if master_package_data is None or len(master_package_data) == 0:
        print("Package not found, returning to main menu!")
        return

    master_package = package_manager.PackageManager("NuGet")
    master_package.initialize_from_nuget_data(master_package_data)
    generate_catalog_data(master_package, "")
    print("What would you like to do: ")
    while True:
        choice = input(
            "1. Display Package Details\n2. Generate Dependency Tree\n3. Return to Main Menu: "
        )
        if choice == "1":
            master_package.print_package_data()
            print("\n")
        elif choice == "2":
            while True:
                sub_choice = input(
                    "1. Generate Dependency Tree for latest version\n2. Generate Dependency Tree for a specific version\n3. Return to previous Menu: "
                )
                if sub_choice == "1":
                    generate_catalog_data(master_package, "")
                    generate_dependency_data(master_package)
                    print("\n")
                elif sub_choice == "2":
                    version = input("Enter the version: ")
                    generate_catalog_data(master_package, version)
                    generate_dependency_data(master_package)
                    print("\n")
                elif sub_choice == "3":
                    break
                else:
                    print("Invalid Choice")

        elif choice == "3":
            return
        else:
            print("Invalid Choice. Please enter the correct choice:")
            continue


def start_npylib():
    print("Welcome to NuGet pyLib Tool.")
    while True:
        choice = input(
            "Do you wish to: \n1. Search for a NuGet package\n2. Build Dependency Tree for solution/csproj\n3. Exit: "
        )

        if choice == "1":
            search()

        elif choice == "2":
            solution_manager.options()

        elif choice == "3":
            print("Terminating script session")
            return

        else:
            print("Invalid choice. Please enter a correct choice.")


if __name__ == "__main__":
    start_npylib()
