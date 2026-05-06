#!/usr/bin/env python3

import argparse
import os
import struct
from xml.sax.saxutils import escape


def load_binary_stl(path: str):
    with open(path, 'rb') as f:
        f.read(80)
        tri_count = struct.unpack('<I', f.read(4))[0]
        vertices = []
        normals = []
        vertex_map = {}
        normal_map = {}
        indices = []
        for _ in range(tri_count):
            normal = struct.unpack('<3f', f.read(12))
            if normal not in normal_map:
                normal_map[normal] = len(normals) // 3
                normals.extend(normal)
            normal_idx = normal_map[normal]
            tri_vertices = []
            for _ in range(3):
                tri_vertices.append(struct.unpack('<3f', f.read(12)))
            f.read(2)
            for vertex in tri_vertices:
                if vertex not in vertex_map:
                    vertex_map[vertex] = len(vertices) // 3
                    vertices.extend(vertex)
                vertex_idx = vertex_map[vertex]
                indices.extend([vertex_idx, normal_idx])
        return vertices, normals, indices, tri_count


def build_dae(mesh_name: str, vertices, normals, indices, tri_count: int, rgba: str) -> str:
    pos_count = len(vertices)
    normal_count = len(normals)
    vertices_text = ' '.join(f'{v:.9g}' for v in vertices)
    normals_text = ' '.join(f'{n:.9g}' for n in normals)
    indices_text = ' '.join(str(i) for i in indices)
    mesh_id = escape(mesh_name)
    effect_id = f'{mesh_id}_effect'
    material_id = f'{mesh_id}_material'
    geometry_id = f'{mesh_id}_geometry'
    vertices_id = f'{mesh_id}_vertices'
    pos_id = f'{mesh_id}_positions'
    normal_id = f'{mesh_id}_normals'
    return f'''<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset>
    <contributor>
      <authoring_tool>rdd_description stl_to_dae</authoring_tool>
    </contributor>
    <created>2026-04-28T00:00:00Z</created>
    <modified>2026-04-28T00:00:00Z</modified>
    <unit name="meter" meter="1"/>
    <up_axis>Z_UP</up_axis>
  </asset>
  <library_effects>
    <effect id="{effect_id}">
      <profile_COMMON>
        <technique sid="common">
          <phong>
            <emission><color>0 0 0 1</color></emission>
            <ambient><color>{rgba}</color></ambient>
            <diffuse><color>{rgba}</color></diffuse>
            <specular><color>0.04 0.04 0.04 1</color></specular>
            <shininess><float>10.0</float></shininess>
            <index_of_refraction><float>1.0</float></index_of_refraction>
          </phong>
        </technique>
      </profile_COMMON>
    </effect>
  </library_effects>
  <library_materials>
    <material id="{material_id}" name="{material_id}">
      <instance_effect url="#{effect_id}"/>
    </material>
  </library_materials>
  <library_geometries>
    <geometry id="{geometry_id}" name="{geometry_id}">
      <mesh>
        <source id="{pos_id}">
          <float_array id="{pos_id}_array" count="{pos_count}">{vertices_text}</float_array>
          <technique_common>
            <accessor source="#{pos_id}_array" count="{pos_count // 3}" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <source id="{normal_id}">
          <float_array id="{normal_id}_array" count="{normal_count}">{normals_text}</float_array>
          <technique_common>
            <accessor source="#{normal_id}_array" count="{normal_count // 3}" stride="3">
              <param name="X" type="float"/>
              <param name="Y" type="float"/>
              <param name="Z" type="float"/>
            </accessor>
          </technique_common>
        </source>
        <vertices id="{vertices_id}">
          <input semantic="POSITION" source="#{pos_id}"/>
        </vertices>
        <triangles count="{tri_count}" material="{material_id}">
          <input semantic="VERTEX" source="#{vertices_id}" offset="0"/>
          <input semantic="NORMAL" source="#{normal_id}" offset="1"/>
          <p>{indices_text}</p>
        </triangles>
      </mesh>
    </geometry>
  </library_geometries>
  <library_visual_scenes>
    <visual_scene id="Scene" name="Scene">
      <node id="{mesh_id}" name="{mesh_id}" type="NODE">
        <instance_geometry url="#{geometry_id}">
          <bind_material>
            <technique_common>
              <instance_material symbol="{material_id}" target="#{material_id}"/>
            </technique_common>
          </bind_material>
        </instance_geometry>
      </node>
    </visual_scene>
  </library_visual_scenes>
  <scene>
    <instance_visual_scene url="#Scene"/>
  </scene>
</COLLADA>
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src')
    parser.add_argument('dst')
    parser.add_argument('--rgba', required=True, help='e.g. "0.04 0.04 0.04 1"')
    args = parser.parse_args()

    vertices, normals, indices, tri_count = load_binary_stl(args.src)
    mesh_name = os.path.splitext(os.path.basename(args.dst))[0]
    dae = build_dae(mesh_name, vertices, normals, indices, tri_count, args.rgba)
    with open(args.dst, 'w', encoding='utf-8') as f:
        f.write(dae)


if __name__ == '__main__':
    main()
