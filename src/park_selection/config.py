from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = PROJECT_ROOT / "dataset_structured"
PROCESSED_DIR = DATASET_ROOT / "05_processed"
LAYERS_DIR = PROCESSED_DIR / "standardized_layers"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

DEFAULT_DEMAND_PATH = LAYERS_DIR / "elderly_demand_3857.shp"
DEFAULT_PARKS_PATH = LAYERS_DIR / "parks_with_quality_3857.shp"
DEFAULT_POIS_PATH = LAYERS_DIR / "pois_3857.shp"
DEFAULT_PARK_POLYGONS_PATH = LAYERS_DIR / "parks_poly_3857.shp"
DEFAULT_CANDIDATES_PATH = LAYERS_DIR / "candidate_new_park_spots.shp"
REPORT_PARKS_PATH = OUTPUT_DIR / "parks_with_quality_report.gpkg"
REPORT_CANDIDATES_PATH = OUTPUT_DIR / "candidate_new_park_spots.gpkg"
POI_SPLITS_GLOB = str(DATASET_ROOT / "01_tabular" / "poi_converted_wgs" / "splits" / "poi_converted_wgs_part_*.csv")
DEFAULT_CLEANED_POI_CSV = PROCESSED_DIR / "cleaned_target_pois.csv"

CENTRAL_DISTRICTS = ["黄浦区", "徐汇区", "长宁区", "静安区", "普陀区", "虹口区", "杨浦区"]

REPORT_CATCHMENT_M = 1_500.0
REPORT_DECAY_SIGMA_M = 750.0
QUALITY_SUPPORT_BUFFER_M = 500.0

UPGRADE_DELTA = 0.10
SUPPORT_DELTA = 0.07
NEW_PARK_DELTA = 0.18

UPGRADE_COST = 3
SUPPORT_COST = 2
NEW_PARK_COST = 5
TOTAL_BUDGET = 100

DEMAND_COLUMNS = [
    "elderly_demand",
    "elderly_de",
    "elderly_count",
    "elderly_co",
    "Di",
]
POPULATION_COLUMNS = ["population", "Population", "pop"]
ELDERLY_RATIO_COLUMNS = ["elder_rati", "elderly_ratio", "Elderly_pe", "ElderlyRatio"]

QUALITY_COLUMNS = ["park_quality", "Qj_index", "norm_Qj", "quality", "Qj"]
PARK_NAME_COLUMNS = ["park_name", "name", "NAME", "Name"]
DISTRICT_COLUMNS = ["district", "区县", "adname", "District"]

TRANSIT_SUBCATEGORIES = {"公交站", "地铁", "地铁站"}
TOILET_SUBCATEGORIES = {"公厕"}
HEALTH_KEYWORDS = ["综合医院", "社区医疗", "诊所", "急救中心", "药店", "医院", "卫生服务中心", "卫生院"]
ELDERLY_SERVICE_INCLUDE_KEYWORDS = [
    "老年大学",
    "老年活动",
    "养老院",
    "敬老院",
    "养护院",
    "颐养院",
    "长者照护",
    "照护之家",
    "日间照护",
    "日间服务",
    "助餐",
    "为老服务",
    "护理院",
    "福利院",
]
ELDERLY_SERVICE_EXCLUDE_KEYWORDS = ["宠物", "动物医疗", "兽医", "宠物用品", "成人"]
