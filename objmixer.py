#!/usr/bin/env python3

import argparse, sys, re, enum, io
from typing import BinaryIO, Tuple

class RecordType(enum.Enum):
    position, normal, texcoord, triangle = range(4)

class VertexObject(object):
    def __init__(self):
        self.position:tuple[float, float, float] = (0, 0, 0)
        self.normal:tuple[float, float, float] = (0, 0, 0)
        self.texcoord:tuple[float, float] = (0, 0)
        self.index:int = 0

class MeshObject(object):
    def __init__(self, file_path:str):
        self.triangles:list[tuple[VertexObject, VertexObject, VertexObject]] = []
        with open(file_path, mode='rb') as fp:
            self.__load(buffer=fp)

    def __load(self, buffer:BinaryIO):
        value, record = b'', []
        value_type:RecordType = RecordType.position
        prev = b''
        vertex:VertexObject = None
        vertex_idx:int = 0
        vertex_map:dict[int, VertexObject] = {}
        while True:
            char = buffer.read(1)
            if not char: break
            if char == b'v': pass
            elif char == b'n':
                if prev == b'v': value_type = RecordType.normal
            elif char == b't':
                if prev == b'v': value_type = RecordType.texcoord
            elif char == b'f':
                if prev == b'\n':value_type = RecordType.triangle
            elif char in b' \n':
                if prev == b'v':
                    vertex_idx += 1
                    value_type = RecordType.position
                    vertex = VertexObject()
                    vertex.index = vertex_idx
                    vertex_map[vertex.index] = vertex
                elif prev == b' ':pass
                else:
                    if value:
                        if value_type == RecordType.triangle:
                            record.append(int(value.split(b'/')[0]))
                        else:
                            record.append(float(value))
                value = b''
                if char == b'\n':
                    if value_type == RecordType.normal:
                        vertex.normal = tuple(record)
                    elif value_type == RecordType.position:
                        vertex.position = tuple(record)
                    elif value_type == RecordType.texcoord:
                        if len(record) == 2: vertex.texcoord = tuple(record)
                    elif value_type == RecordType.triangle:
                        triangle = tuple(vertex_map.get(x) for x in record) # type:tuple[VertexObject,VertexObject,VertexObject]
                        if triangle: self.triangles.append(triangle)
                    record = []
            elif char == b'#':
                while True:
                    char = buffer.read(1)
                    if not char or char == b'\n': break
            else:
                value += char
            prev = char
        print('# vertices:{} triangles:{}'.format(len(vertex_map), len(self.triangles)))

    def __encode_tuple(self, buffer:io.StringIO, data:Tuple[float, ...]):
        for value in data: buffer.write(' {:.7f}'.format(value))

    def dump(self):
        buffer:io.StringIO = io.StringIO()
        vertex_array:list[VertexObject] = []
        hash_map = {}
        for triangle in self.triangles:
            for vertex in triangle:
                uuid = vertex.__hash__()
                if uuid not in hash_map:
                    vertex_array.append(vertex)
                    vertex.index = len(vertex_array)
                    hash_map[uuid] = vertex
        for vertex in vertex_array:
            buffer.write('v')
            self.__encode_tuple(buffer, vertex.position)
            buffer.write('\n')
            if vertex.normal:
                buffer.write('vn')
                self.__encode_tuple(buffer, vertex.normal)
                buffer.write('\n')
            if vertex.texcoord:
                buffer.write('vt')
                self.__encode_tuple(buffer, vertex.texcoord)
                buffer.write('\n')
        buffer.write('# {} verticies\n'.format(len(vertex_array)))
        for triangle in self.triangles:
            buffer.write('f')
            for vertex in triangle: buffer.write(' {}/{}/{}'.format(vertex.index, vertex.index, vertex.index))
            buffer.write('\n')
        buffer.write('# {} elements\n'.format(len(self.triangles)))
        buffer.seek(0)
        return buffer.read()

    def append(self, target: 'MeshObject'):
        for triangle in target.triangles:
            self.triangles.append(triangle)


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--obj-file', '-f', nargs='+', required=True)
    options = arguments.parse_args(sys.argv[1:])
    mesh:MeshObject = None
    for item_path in options.obj_file:
        item = MeshObject(file_path=item_path)
        if not mesh:
            mesh = item
            continue
        mesh.append(item)
    print(mesh.dump())
