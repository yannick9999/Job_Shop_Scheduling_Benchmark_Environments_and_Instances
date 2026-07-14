from data.data_parsers.parser_fjsp import parse_fjsp
from scheduling_environment.jobShop import JobShop
from solution_methods.cp_sat.run_cp_sat import run_CP_SAT
from visualization import gantt_chart

parameters = {
    "solver": {
        "time_limit": 3600,
        "model": "fjsp",
    },
}

jobShopEnv = parse_fjsp(JobShop(), '/fjsp/example_3x3.fjs')
results, jobShopEnv = run_CP_SAT(jobShopEnv, **parameters)
plt = gantt_chart.plot(jobShopEnv)
plt.savefig('example_3x3_gantt.pdf')
plt.savefig('example_3x3_gantt.png')
