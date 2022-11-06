class PackageManager:
    class PackageDependency:
        class Range:
            def set_range_from_string(self, s):
                """
                Initializes version range of version
                :param s: The version range in string. Sample Examples:
                    "[4.3.1, 4.3.1]"    The first one indicates the base and the last indicates the ceil version
                    "[3.3.3, )"
                """
                s = s.replace("[", "")
                s = s.replace("]", "")
                s = s.replace("(", "")
                s = s.replace(")", "")
                s = s.split(",")
                self.Base = s[0]
                if len(s) > 1:
                    self.Ceil = s[1]
                else:
                    self.Ceil = s[0]

            def __init__(self):
                self.Base = "0.0.1"
                self.Ceil = "0.0.1"

        def __init__(self, dependency_data):
            """
            Initializes the Package dependency. This class represents a single dependency
            :param dependency_data: A dictionary containing the following as keys:
            @id   : The rest ID of the master package
            id    : The name of the dependency package
            range : The version range
            """
            # this is done for nuget search as well as csproj
            self.PackageName = ""
            self.VersionRange = ""
            if "id" in dependency_data:
                self.PackageName = dependency_data["id"]
            elif "@Include" in dependency_data:
                self.PackageName = dependency_data["@Include"]
            if "range" in dependency_data:
                self.VersionRange = self.Range()
                self.VersionRange.set_range_from_string(dependency_data["range"])
            elif "@Version" in dependency_data:
                self.VersionRange = self.Range()
                self.VersionRange.set_range_from_string(dependency_data["@Version"])
            elif "Version" in dependency_data:
                self.VersionRange = self.Range()
                self.VersionRange.set_range_from_string(dependency_data["Version"])
            if "@id" in dependency_data:
                self.DependencyRESTId = dependency_data["@id"]

    class PackageVersion:
        def __init__(self, version, version_rest_id, downloads):
            """
            Initializes the Package Version data. This class represents a single version of a package
            :param version: The version in string
            :param version_rest_id: The rest id url of the version.
            :param downloads: The number of downloads
            """
            self.Version = version
            self.VersionRestID = version_rest_id
            self.Downloads = downloads

    def __init__(self, data_type):
        self.DataType = data_type
        self.Name = ""
        self.Title = ""
        # stores the NuGet Dependencies
        self.NuGetDependencies = {}
        # only for csproj
        self.ProjectReferences = []
        self.PackageReferences = {}
        self.SupportedFrameworks = []
        # Framework under consideration
        self.Framework = ""
        self.PackageMasterRestID = ""
        self.Authors = ""
        self.LatestVersion = ""
        self.Type = ""
        self.Title = ""
        self.Description = ""
        self.Summary = ""
        self.LicenseURL = ""
        self.ProjectURL = ""
        self.Tags = ""
        self.Authors = ""
        self.Owners = ""
        self.RegistrationManifest = ""
        self.TotalDownloads = ""
        self.Verified = ""
        self.Version = ""
        self.Versions = {}
        self.PackageVersionURL = ""
        self.VersionDownloads = ""
        self.Version = ""

    def initialize_from_nuget_data(self, package_data):
        self.DataType = "nuget"
        self.Name = package_data["id"]
        self.PackageMasterRestID = package_data["@id"]
        self.Authors = package_data["authors"]
        self.LatestVersion = package_data["version"]
        self.Type = package_data["@type"]
        self.Title = package_data["title"]
        self.Description = package_data["description"]
        self.Summary = package_data["summary"]
        self.LicenseURL = package_data["licenseUrl"]
        self.ProjectURL = package_data["projectUrl"]
        self.Tags = package_data["tags"]
        self.Authors = package_data["authors"]
        self.Owners = package_data["owners"]
        self.RegistrationManifest = package_data["registration"]
        self.TotalDownloads = package_data["totalDownloads"]
        self.Verified = package_data["verified"]
        self.Version = package_data["version"]

        for version in package_data["versions"]:
            self.Versions[version["version"]] = (version["@id"], version["downloads"])
            if self.LatestVersion == version["version"]:
                self.PackageVersionURL = version["@id"]
                self.VersionDownloads = version["downloads"]

    def initialize_from_csproj(self, csproj_data):
        self.DataType = "csproj"
        self.NuGetDependencies = {}
        self.SupportedFrameworks = []
        if "Project" not in csproj_data:
            print("Project details not available!")
            return None

        if "PropertyGroup" in csproj_data["Project"]:
            # PropertyGroup can be one instance: dict or can be in multiples: list
            if isinstance(csproj_data["Project"]["PropertyGroup"], (dict)):
                # single unit
                if "TargetFramework" in csproj_data["Project"]["PropertyGroup"]:
                    target_framework = (
                        "." + csproj_data["Project"]["PropertyGroup"]["TargetFramework"]
                    )
                    self.SupportedFrameworks.extend(target_framework.split(","))
                elif (
                    "TargetFrameworkVersion" in csproj_data["Project"]["PropertyGroup"]
                ):
                    target_framework = (
                        ".NETFramework"
                        + csproj_data["Project"]["PropertyGroup"][
                            "TargetFrameworkVersion"
                        ]
                    )
                    self.SupportedFrameworks.extend(target_framework)

                # add the assembly name
                if "Copyright" in csproj_data["Project"]["PropertyGroup"]:
                    if (
                        "AssemblyName"
                        in csproj_data["Project"]["PropertyGroup"]["Copyright"]
                    ):
                        self.Name = csproj_data["Project"]["PropertyGroup"][
                            "Copyright"
                        ]["AssemblyName"]

            elif isinstance(csproj_data["Project"]["PropertyGroup"], (list)):
                for property_group in csproj_data["Project"]["PropertyGroup"]:
                    if property_group is not None:
                        if "TargetFramework" in property_group:
                            frameworks = property_group["TargetFramework"].split(",")
                            for i in range(len(frameworks)):
                                frameworks[i] = "." + frameworks[i]
                            self.SupportedFrameworks.extend(frameworks)
                        elif "TargetFrameworkVersion" in property_group:
                            frameworks = property_group["TargetFrameworkVersion"].split(",")
                            for i in range(len(frameworks)):
                                f = frameworks[i].strip()
                                if f[0] == "v":
                                    f = f[1:]
                                frameworks[i] = ".NETFramework " + f
                            self.SupportedFrameworks.extend(frameworks)

        if "ItemGroup" not in csproj_data["Project"]:
            print("Item Group not available!")
            return None

        def return_csproj_name_from_path(csproj_path):
            bindex = csproj_path.rfind("\\")
            name = csproj_path[bindex + 1 :]
            name = name.replace(".csproj", "")
            return name

        # generate the dependencies
        dependency_list = []
        # ItemGroup can be one instance: dict or can be in multiples: list
        if isinstance(csproj_data["Project"]["ItemGroup"], (dict)):
            # if dictionary, get the PackageReference for NuGet
            item_group = csproj_data["Project"]["ItemGroup"]
            if "PackageReference" in item_group:
                for pkg_reference in csproj_data["Project"]["ItemGroup"][
                    "PackageReference"
                ]:
                    dependency_list.append(self.PackageDependency(pkg_reference))

            if "ProjectReference" in item_group:
                if isinstance(item_group["ProjectReference"], (dict)):
                    project_reference = item_group["ProjectReference"]
                    self.ProjectReferences.append(
                        return_csproj_name_from_path(project_reference["@Include"])
                    )
                elif isinstance(item_group["ProjectReference"], (list)):
                    for project_reference in item_group["ProjectReference"]:
                        self.ProjectReferences.append(
                            return_csproj_name_from_path(project_reference["@Include"])
                        )

        elif isinstance(csproj_data["Project"]["ItemGroup"], (list)):
            for item_group in csproj_data["Project"]["ItemGroup"]:
                if item_group is not None:
                    if "PackageReference" in item_group:
                        if isinstance(item_group["PackageReference"], (list)):
                            for pkg_reference in item_group["PackageReference"]:
                                dependency_list.append(self.PackageDependency(pkg_reference))
                        elif isinstance(item_group["PackageReference"], (dict)):
                            pkg_reference = item_group["PackageReference"]
                            dependency_list.append(self.PackageDependency(pkg_reference))

                    if "ProjectReference" in item_group:
                        if isinstance(item_group["ProjectReference"], (dict)):
                            project_reference = item_group["ProjectReference"]
                            self.ProjectReferences.append(
                                return_csproj_name_from_path(project_reference["@Include"])
                            )
                        elif isinstance(item_group["ProjectReference"], (list)):
                            for project_reference in item_group["ProjectReference"]:
                                self.ProjectReferences.append(
                                    return_csproj_name_from_path(
                                        project_reference["@Include"]
                                    )
                                )

        for framework in self.SupportedFrameworks:
            self.NuGetDependencies[framework] = dependency_list

        # hack to initialize framework with the first one
        if len(self.SupportedFrameworks) > 0:
            self.Framework = self.SupportedFrameworks[0]

    def set_package_version(self, version):
        if version not in self.Versions:
            return "Version not available"

        version_data = self.Versions[version]
        self.PackageVersionURL = version_data[0]
        self.VersionDownloads = version_data[1]
        self.Version = version

    def set_catalog_data_json(self, catalog_data):
        self.CeationTimestamp = catalog_data["created"]
        self.PackageHash = catalog_data["packageHash"]
        self.PackageSize = catalog_data["packageSize"]
        self.SupportedFrameworks = []

        if "dependencyGroups" in catalog_data:
            for framework_dependencies in catalog_data["dependencyGroups"]:
                framework = framework_dependencies["targetFramework"]
                self.SupportedFrameworks.append(framework)
                if "dependencies" in framework_dependencies:
                    dependency_list = []
                    for dependencies in framework_dependencies["dependencies"]:
                        dependency_list.append(self.PackageDependency(dependencies))
                    self.NuGetDependencies[framework] = dependency_list
                else:
                    self.NuGetDependencies[framework] = []
        else:
            self.NuGetDependencies["N/A"] = []

    def print_package_data(self):
        print("Package Details:")
        print("Name: ", self.Name)
        if self.Title != "":
            print("Title", self.Title)

        print("Supported Frameworks:", self.SupportedFrameworks)
        print("Current Version: ", self.Version)
        if self.Description != "":
            print("Description: ", self.Description)
        if self.Summary != "":
            print("Summary: ", self.Summary)
        if self.Authors != "":
            print("Authors: ", self.Authors)
        if self.Owners != "":
            print("Owners: ", self.Owners)
        if self.TotalDownloads != "":
            print("Total Downloads: ", self.TotalDownloads)
        if self.TotalDownloads != "":
            print("Version Downloads: ", self.VersionDownloads)
        if self.ProjectURL != "":
            print("Project URL: ", self.ProjectURL)
        if self.LicenseURL != "":
            print("License URL: ", self.LicenseURL)

        if len(self.NuGetDependencies) > 0:
            for key in self.NuGetDependencies:
                print(key)
                packages = self.NuGetDependencies[key]
                # get the longest package name
                length = 0
                for p in packages:
                    length = max(len(p.PackageName), length)

                for p in packages:
                    print(
                        "\t"
                        + p.PackageName
                        + (" " * (length - len(p.PackageName)))
                        + " : "
                        + p.VersionRange.Ceil
                        + " - "
                        + p.VersionRange.Base
                    )

    def print_available_frameworks_with_index(self):
        for i in range(len(self.SupportedFrameworks)):
            print(str(i + 1) + ". " + self.SupportedFrameworks[i])
