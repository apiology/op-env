from collections import OrderedDict
import json
import subprocess
from typing import Collection, Dict, List, Mapping, NewType, Sequence, Set, TypeVar

from pydantic import BaseModel

EnvVarName = NewType('EnvVarName', str)
Title = NewType('Title', str)
FieldName = NewType('FieldName', str)
FieldValue = NewType('FieldValue', str)


class OpItemOverview(BaseModel):
    tags: List[EnvVarName]


class OpItemDetailsField(BaseModel):
    designation: str
    name: FieldName
    type: str
    value: FieldValue


class OpItemSectionField(BaseModel):
    t: FieldName
    v: FieldValue


class OpItemSection(BaseModel):
    fields: List[OpItemSectionField] = []


class OpItemDetails(BaseModel):
    fields: List[OpItemDetailsField]
    sections: List[OpItemSection]


class OpListItemsEntry(BaseModel):
    overview: OpItemOverview

    class Config:
        # We'll be parsing this and then feeding it back into op, so
        # let's keep all of the keys, not just the ones we care to
        # view/manipulate.  In particular, I know the the uuid key is
        # required for 'op get item'.
        extra = 'allow'


class OpGetItemEntry(BaseModel):
    overview: OpItemOverview
    details: OpItemDetails


# Data in the format of the output of 'op list items', but guaranteed
# to come in order of the tags provided
OpListItemsOutputOrderedByEnvVarName = NewType('OpListItemsOutputOrderedByEnvVarName',
                                               List[OpListItemsEntry])


class OPLookupError(LookupError):
    pass


class TooManyEntriesOPLookupError(OPLookupError):
    pass


class NoEntriesOPLookupError(OPLookupError):
    pass


class NoFieldValueOPLookupError(OPLookupError):
    pass


class InvalidTagOPLookupError(OPLookupError):
    pass


def _op_list_items(env_var_names: List[EnvVarName]) -> OpListItemsOutputOrderedByEnvVarName:
    list_command = ['op', 'list', 'items', '--tags',
                    ','.join(env_var_names)]
    list_items_json_docs_bytes = subprocess.check_output(list_command)
    # list_items_json_docs_str = list_items_json_docs_bytes.decode('utf-8')
    list_items_data = [
        OpListItemsEntry(**item)
        for item in json.loads(list_items_json_docs_bytes)
    ]
    by_env_var_name: Dict[EnvVarName, OpListItemsEntry] = {}

    #
    # Ensure we have at most one item per env var name
    #
    for entry in list_items_data:
        for env_var_name in entry.overview.tags:
            if env_var_name in by_env_var_name:
                raise TooManyEntriesOPLookupError("Too many 1Password entries "
                                                  f"with tag {env_var_name} found")
            else:
                by_env_var_name[env_var_name] = entry
    ordered_list_items_data = []
    #
    # Ensure we have at least one item per env var name
    #
    for env_var_name in env_var_names:
        if env_var_name not in by_env_var_name:
            raise NoEntriesOPLookupError(f"No 1Password entries with tag {env_var_name} found")
        else:
            ordered_list_items_data.append(by_env_var_name[env_var_name])
    #
    # With exactly one item per env var name, we know this is ordered
    # by the env var name.
    #
    return OpListItemsOutputOrderedByEnvVarName(ordered_list_items_data)


def _fields_from_list_output(list_items_output: OpListItemsOutputOrderedByEnvVarName,
                             env_var_names: Collection[EnvVarName],
                             all_fields_to_seek: Collection[FieldName]) ->\
                               Dict[EnvVarName, Dict[FieldName, FieldValue]]:
    #
    # 'op get item' with the '--fields' flag will take the JSON list
    # of items structure from 'op list items' and return JSON objects
    # separated by newlines of the fields requested if they exist in
    # the item
    #
    sorted_fields_to_seek = sorted(all_fields_to_seek)
    get_command: List[str] = ['op', 'get', 'item', '-', '--fields',
                              ','.join(sorted_fields_to_seek)]
    list_items_output_raw: bytes = json.dumps([
        item.dict() for item in list_items_output
    ]).encode('utf-8')
    field_values_json_docs_bytes = subprocess.check_output(get_command,
                                                           input=list_items_output_raw)
    field_values_json_docs_str = field_values_json_docs_bytes.decode('utf-8')
    field_values_data: List[Dict[FieldName, FieldValue]] = [
        json.loads(field_values_json)
        for field_values_json
        in field_values_json_docs_str.split('\n')
        if field_values_json != ''
    ]
    #
    # Organize the fields found based on what the original tags were
    #
    return {
        env_var_name: field_values
        for (env_var_name, field_values)
        in zip(env_var_names, field_values_data)
    }


def _fields_from_title(title: Title) -> Dict[EnvVarName, FieldValue]:
    get_command: List[str] = ['op', 'get', 'item', title]
    output_bytes = subprocess.check_output(get_command)
    output = OpGetItemEntry(**json.loads(output_bytes))
    overview = output.overview
    tags: List[EnvVarName] = overview.tags
    details = output.details
    regular_field_values: Dict[FieldName, FieldValue] = {
        field.name: field.value
        for field in details.fields
    }
    section_field_values: Dict[FieldName, FieldValue] = {
        field.t: field.v
        for section in details.sections
        for field in section.fields
    }
    field_values = {**section_field_values, **regular_field_values}
    return {
        tag: _op_pluck_correct_field(tag, field_values)
        for tag in tags
    }


def _last_underscored_component_lowercased(env_var_name: EnvVarName) -> FieldName:
    components = env_var_name.split('_')
    return FieldName(components[-1].lower())


def _last_double_underscored_component_lowercased(env_var_name: EnvVarName) -> FieldName:
    components = env_var_name.split('__')
    return FieldName(components[-1].lower())


def _all_lowercased(env_var_name: EnvVarName) -> FieldName:
    return FieldName(env_var_name.lower())


T = TypeVar('T')


def _uniqify(fields: Sequence[T]) -> List[T]:
    "Removes duplicates but preserves order"
    # https://stackoverflow.com/questions/4459703/how-to-make-lists-contain-only-distinct-element-in-python
    return list(OrderedDict.fromkeys(fields))


def _aliases(fields: List[FieldName]) -> List[FieldName]:
    if 'user' in fields:
        return [FieldName('username')]
    else:
        return []


def _op_consolidated_fields(env_var_names: Collection[EnvVarName]) -> Set[FieldName]:
    return {
        field_name
        for env_var_name in env_var_names
        for field_name in _op_fields_to_try(env_var_name)
    }


def _op_fields_to_try(env_var_name: EnvVarName) -> List[FieldName]:
    candidates: List[FieldName] = _uniqify([
        _all_lowercased(env_var_name),
        _last_double_underscored_component_lowercased(env_var_name),
        _last_underscored_component_lowercased(env_var_name),
    ])
    return candidates + _aliases(candidates) + [FieldName('password')]


def _op_pluck_correct_field(env_var_name: EnvVarName,
                            field_values: Dict[FieldName,
                                               FieldValue]) -> FieldValue:
    fields = _op_fields_to_try(env_var_name)
    for field in fields:
        if field in field_values and field_values[field] != '':
            return field_values[field]
    raise NoFieldValueOPLookupError('1Passsword entry with tag '
                                    f'{env_var_name} has no value for '
                                    'the fields tried: '
                                    f'{", ".join(fields)}.  Please populate '
                                    'one of these fields in 1Password.')


def _validate_env_var_names(env_var_names: List[EnvVarName]) -> None:
    for env_var_name in env_var_names:
        if ',' in env_var_name:
            raise InvalidTagOPLookupError('1Password does not support tags with commas')


def _do_env_lookups(env_var_names: List[EnvVarName]) -> Dict[EnvVarName, FieldValue]:
    if len(env_var_names) == 0:
        return {}
    _validate_env_var_names(env_var_names)
    list_items_output = _op_list_items(env_var_names)
    all_fields_to_seek = _op_consolidated_fields(env_var_names)
    field_values_for_envvars: Dict[EnvVarName, Dict[FieldName, FieldValue]] = \
        _fields_from_list_output(list_items_output,
                                 env_var_names,
                                 all_fields_to_seek)
    return {
        env_var_name: _op_pluck_correct_field(env_var_name, field_values_for_envvars[env_var_name])
        for env_var_name in field_values_for_envvars
    }


def _do_title_lookups(titles: List[Title]) -> Mapping[EnvVarName, FieldValue]:
    title_lookups: Dict[EnvVarName, FieldValue] = {}
    for title in titles:
        fields_by_env_name: Dict[EnvVarName, FieldValue] = _fields_from_title(title)
        title_lookups.update(fields_by_env_name)
    return title_lookups


def do_lookups(env_var_names: List[EnvVarName],
               titles: List[Title]) -> Dict[EnvVarName, FieldValue]:
    env_lookups = _do_env_lookups(env_var_names)
    title_lookups = _do_title_lookups(titles)
    return {**env_lookups, **title_lookups}
