import requests


def search_result_manager(search_result_json):
    total_hits = search_result_json["totalHits"]
    print(total_hits, "results found!")

    if total_hits == 0:
        return {}
    search_results_map_by_id = {}
    search_results_map_by_index = {}

    index = 1

    for data in search_result_json["data"]:
        search_results_map_by_id[data["id"]] = data
        search_results_map_by_index[str(index)] = data["id"]
        index = index + 1

    loaded_result_count = index

    print("Loaded " + str(index - 1) + " results. Showing 20 rows at an instance")

    # iterate for the results
    start = 1
    end = 20 if 20 < loaded_result_count else loaded_result_count

    while True:

        for i in range(start, end + 1):
            if i < loaded_result_count:
                print(str(i) + ". " + search_results_map_by_index[str(i)])

        while True:
            choice = input(
                "Enter the serial number to continue with the result, or press M to load more results. "
                "Press E to exit to main menu: "
            )
            # exit
            if choice == "E":
                return

            elif choice == "M" or choice == "m":
                # load more results.

                if end == loaded_result_count:
                    print("No more results to show. Loaded the last chunk")
                    pass

                start = end + 1
                end = (
                    end + 20 if end + 20 < loaded_result_count else loaded_result_count
                )

                break

            # get the result and return
            elif 1 <= int(choice) <= end:
                print(
                    "Selecting "
                    + choice
                    + ". "
                    + search_results_map_by_index[str(choice)]
                )
                # return the id and create a map
                return search_results_map_by_id[
                    search_results_map_by_index[str(choice)]
                ]
            else:
                print("Invalid Choice!")


def search_package(
    query, skip=0, take=500, pre_release=False, sem_ver_level=None, package_type=None
):
    """
    :param query: The search keyword
    :param skip: skip number entries
    :param take: entries to add to the result
    :param pre_release: defines whether to retrieve pre-release data
    :param sem_ver_level:
    :param package_type:
    :return: returns the response.json on success
    """
    search_url = (
        "https://azuresearch-usnc.nuget.org/query?q="
        + query
        + "&skip="
        + str(skip)
        + "&take="
        + str(take)
        + "&prerelease="
        + str(pre_release)
    )
    if sem_ver_level is not None:
        search_url = search_url + "&semVerLevel=" + sem_ver_level
    if package_type is not None:
        search_url = search_url + "&packageType=" + package_type

    print("Nuget Package Request URL: ", search_url)
    response = requests.get(search_url)
    if response.status_code == 200:
        return response.json()
    else:
        return {}


def search_and_auto_generate_data(query, version):
    result_json = search_package(query, take=5, sem_ver_level=version)
    package_data = {}
    for data in result_json["data"]:
        if str.lower(data["id"]) == str.lower(query):
            package_data = data
            print("Package found: ", data["id"])
            break

    # print(package_data)
    return package_data


def search_by_title(query):
    """

    :param query: The title to search for
    :return: the response json
    """
    return search_result_manager(search_package(query))


def get_catalog_entry_by_version_url(package_version_url):
    print("Package Version Request URL: ", package_version_url)

    response = requests.get(package_version_url)

    print(response)
    # print(response.json())

    if response.status_code == 200:

        payload = response.json()

        if "catalogEntry" in payload:
            catalog_url = payload["catalogEntry"]
            print("Catalog Entry Request URL: ", catalog_url)
            response = requests.get(catalog_url)

            print(response)
            # print(response.json())
            return response.json()
