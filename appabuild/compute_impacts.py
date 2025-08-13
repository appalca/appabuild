import bw2data as bd
import lca_algebraic as agb
import yaml

from appabuild.config.lca import LCAConfig
from appabuild.database.databases import parameters_registry
from appabuild.setup import initialize


def compute_impacts(appa_lca_path, lca_path, params_values_path):
    fb_db = initialize(appa_lca_path)

    lca_config = LCAConfig.from_yaml(lca_path)
    fb_db.set_functional_unit(lca_config.scope.fu.name, lca_config.model.parameters)

    fb_db.execute_at_build_time()

    print(bd.databases)

    for param in parameters_registry.values():
        if param.type == "enum":
            agb.newEnumParam(param.name, values=param.weights, default=param.default)
        else:
            agb.newFloatParam(
                param.name,
                default=param.default,
                min=param.min,
                max=param.max,
                distrib=param.distrib,
            )

    fu = agb.findActivity(fb_db.fu_name, db_name=fb_db.name)

    impacts = agb.findMethods("climate change", mainCat="EF v3.0")
    print(f"Selected methods: {impacts}")

    with open(params_values_path, "r") as file:
        params_values = yaml.safe_load(file)

    scores = agb.compute_impacts(fu, impacts, **params_values)
    print("Computed scores:")
    for key, value in scores.to_dict().items():
        print(f"{key}: {value}")
