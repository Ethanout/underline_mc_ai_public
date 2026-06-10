function u.math:__unload__
function u.math:__load__/init_constants
forceload add -1 -1 1 1
summon marker 0.0 0.0 0.0 {UUID: [I; 357754430, -717076478, -1194552630, -574838091], Tags: ["u.math"]}
data modify storage u.math:constant __error__ set value [{type: "default", value: 0}, {type: "division_by_zero", text: '"Division by zero."', value: 1}, {type: "invalid", text: '"Undefined math calculation."', value: 2}, {type: "overflow", text: '"The result is out of range."', value: 4}, {type: "underflow", text: '"The result is too close to zero."', value: 8}, {type: "inexact", text: '"The result may have slight or significant error."', value: 16}, {type: "all_except", value: 31}]
data modify storage u.math:variable context set value {pos: [0.0d, 0.0d, 0.0d], pos1: [0.0d, 0.0d, 0.0d], q: [0.0d, 0.0d, 0.0d, 1.0d]}
say u.math reloaded
