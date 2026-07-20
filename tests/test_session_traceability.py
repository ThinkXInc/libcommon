# tests/test_session_traceability.py
#
# Enforces executable pytest coverage for every registered auth-spec Session requirement.

import ast
import warnings
from pathlib import Path

from session_negative_requirements import SESSION_NEGATIVE_REQUIREMENTS


SESSION_TEST_PATH = Path(__file__).with_name('test_char_session.py')
SESSION_TEST_PREFIX = 'test_negative_session_'


def _test_functions():
    module = ast.parse(SESSION_TEST_PATH.read_text())
    return {
        node.name: node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _session_api_calls(test_function):
    calls = set()
    for node in ast.walk(test_function):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'Session':
            calls.add(node.func.attr)
    return calls


def test_session_negative_requirements_are_collected_executable_tests(request):
    collected = {
        item.name: item
        for item in request.session.items
        if item.path == SESSION_TEST_PATH
    }
    functions = _test_functions()

    for requirement_id, requirement in SESSION_NEGATIVE_REQUIREMENTS.items():
        test_name = requirement['test']
        assert test_name in functions, f'{requirement_id} has no test function: {test_name}'
        assert test_name in collected, f'{requirement_id} is not collected by pytest: {test_name}'

        item = collected[test_name]
        assert item.get_closest_marker('skip') is None, f'{requirement_id} is skipped: {test_name}'
        assert item.get_closest_marker('skipif') is None, f'{requirement_id} is conditionally skipped: {test_name}'

        test_function = functions[test_name]
        assert any(isinstance(node, ast.Assert) for node in ast.walk(test_function)), \
            f'{requirement_id} has no assertion: {test_name}'
        calls = _session_api_calls(test_function)
        missing_apis = requirement['session_apis'] - calls
        assert not missing_apis, f'{requirement_id} does not exercise Session APIs: {sorted(missing_apis)}'


def test_session_negative_tests_are_registered():
    functions = _test_functions()
    registered = {
        requirement['test']
        for requirement in SESSION_NEGATIVE_REQUIREMENTS.values()
    }
    unregistered = sorted(
        name
        for name in functions
        if name.startswith(SESSION_TEST_PREFIX) and name not in registered
    )
    if unregistered:
        warnings.warn(
            f'Session negative tests missing specification registration: {unregistered}',
            stacklevel=1,
        )
