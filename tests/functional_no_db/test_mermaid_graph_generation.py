"""
This module contains the tests for the generation of mermaid graphs.
"""

import os
import re

import pytest

from appabuild.model.graph import build_mermaid_graph
from tests import DATA_DIR


def test_not_found_root_path():
    """
    Check an exception is raised when the root path
    of the foreground datasets can't be found.
    """
    with pytest.raises(ValueError):
        build_mermaid_graph("non_existing_path/", "nvidia_ai_gpu_chip")


def test_no_datasets():
    """
    Check an exception is raised when there is
    no foreground datasets to use to build the graph.
    """
    with pytest.raises(ValueError):
        root_path = os.path.join(DATA_DIR, "graphs_generation", "no_datasets")
        build_mermaid_graph(root_path, "nvidia_ai_gpu_chip")


def test_fu_not_found():
    """
    Check an exception is raised when the functional
    unit to use to build the graph can't be found in
    the loaded foreground datasets.
    """
    with pytest.raises(ValueError):
        root_path = os.path.join(DATA_DIR, "graphs_generation", "valid_datasets")
        build_mermaid_graph(root_path, "amd_ai_gpu_chip")


def extract_params(line: str):
    line = line.strip()
    matching_regex = "\\w+=f\\([\\w+|,]*\\)"
    params = []
    matches = []
    if len(line) > 0:
        if "=f" in line:
            without_matching = re.sub(matching_regex + ",?", "", line)

            matches = []
            for matching in re.findall(matching_regex, line):
                matching = matching.replace(")", "").replace("=f(", ",")
                values = matching.split(",")
                values = [values[0]] + sorted(values[1:])
                matches.append(tuple(values))

            params = without_matching.split(",")
        else:
            params = line.split(",")

    return params, matches


def transform_graph(graph: str):
    graph = graph.replace('"', "")
    lines = graph.split("\n")
    lines.pop(0)
    lines = [line.strip() for line in lines]

    result = []

    for line in lines:
        parts = line.split("|") if "|" in line else line.replace("-->", "||").split("|")
        begin = parts[0].replace("-->", "").strip()
        end = parts[2].strip()

        params, matches = extract_params(parts[1])
        result.append(
            {"begin": begin, "end": end, "params": params, "matches": matches}
        )

    return result


def test_valid_graph():
    """
    Check a graph is correctly build for a set of foreground datasets and
    a functional unit.
    """
    root_path = os.path.join(DATA_DIR, "graphs_generation", "valid_datasets")
    graph = build_mermaid_graph(root_path, "nvidia_ai_gpu_chip")
    graph = transform_graph(graph.script)

    with open(
        os.path.join(DATA_DIR, "graphs_generation", "expected_graph.txt"), "r"
    ) as file:
        expected_graph = file.read()
    expected_graph = transform_graph(expected_graph)

    assert len(expected_graph) == len(graph)

    expected_graph = sorted(expected_graph, key=lambda e: e["begin"] + e["end"])
    graph = sorted(graph, key=lambda e: e["begin"] + e["end"])

    for expected, elem in zip(expected_graph, graph):
        assert elem["begin"] == expected["begin"]
        assert elem["end"] == expected["end"]

        if len(expected["params"]) > 0:
            assert set(elem["params"]) == set(
                expected["params"]
            ), f'missing parameter matching for the link {elem["begin"]} -> {elem["end"]}'

        if len(expected["matches"]) > 0:
            assert set(elem["matches"]) == set(
                expected["matches"]
            ), f'missing parameter matching for the link {elem["begin"]} ->{elem["end"]}'
