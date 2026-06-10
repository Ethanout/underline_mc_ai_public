
SCALE_CONST = 10000
DIRECTION_CONST = 5e-324
COORDINATE_CONST = 8.98846567431158e307/SCALE_CONST
MAGNITUDE_CONST = 2251799813685248

for scale,scaletext in ((1,'0'),(256,'1'),(65536,'2'),(16777216,'3')):
    for directiontext,directionformat in (('left','%s,0,0'),('up','0,%s,0'),('forward','0,0,%s')):
        for axistext,axisformat in (('x','%s,0,0'),('y','0,%s,0'),('z','0,0,%s')):
            for sign,signtext in ((1,'plus'),(-1,'minus')):
                if directiontext == 'left' and axistext == 'y':
                    continue
                with open(f'scale{scaletext}_{directiontext}_{axistext}_{signtext}.json','w') as f:
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
    directionformat%(sign*DIRECTION_CONST),
    axisformat%COORDINATE_CONST,
    scale*MAGNITUDE_CONST,
    scale*MAGNITUDE_CONST
)
                    )



