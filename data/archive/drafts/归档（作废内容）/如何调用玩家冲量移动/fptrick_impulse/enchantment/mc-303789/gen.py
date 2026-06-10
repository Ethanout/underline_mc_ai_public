
for scale,scaletext in ((1,'0'),(256,'1'),(65536,'2'),(16777216,'3')):
    for axistext,axisformat,magicdirection in (('x','%s,0,0','-1,-1.6331238640577083e+16,0'),('y','0,%s,0','0,0,1'),('z','0,0,%s','-1.6331238640577083e+16,1,0')):
        for sign,signtext in ((1,'plus'),(-1,'minus')):
            with open(f'scale{scaletext}_{axistext}_{signtext}.json','w') as f:
                f.write(
"""{
  "description": "",
  "supported_items": [],
  "weight": 1,
  "max_level": 1,
  "min_cost": {"base": 0, "per_level_above_first": 0},
  "max_cost": {"base": 0, "per_level_above_first": 0},
  "anvil_cost": 0,
  "slots": ["saddle"],
  "effects": {
    "location_changed": [
      {
        "effect": {
          "type": "apply_impulse",
          "direction": [%s],
          "coordinate_scale": [%s],
          "magnitude": {
            "type": "linear",
            "base": %s,
            "per_level_above_first": %s
          }
        }
      },
      {
        "effect": {
          "type": "run_function",
          "function": "fptrick_impulse:reset"
        }
      }
    ]
  }
}
""" % (
    magicdirection,
    axisformat%(sign/10000),
    scale,
    scale
)
        )



