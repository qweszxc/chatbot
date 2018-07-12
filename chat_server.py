from flask import Flask
from flask import request
from rasa_nlu.model import Interpreter
import redis
import pymysql
import json
app = Flask(__name__)
model_directory = ".//models//ivr//demo"
interpreter = Interpreter.load(model_directory)
pool = redis.ConnectionPool(host='120.79.80.186', port=6381)
r = redis.Redis(connection_pool=pool)
db = pymysql.connect("120.79.154.149", "root", "zhaozhiwen030609", "hospital")
cursor = db.cursor()


class MedicineSearch:
    user_id = None
    time = None
    name = 'medicine_search'

    def __init__(self):
        self.user_id = None
        self.time = None
        self.name = 'medicine_search'

    def obj_2_json(self):
        return {
            'user_id': self.user_id,
            'time': self.time,
            'name': self.name
        }

    def json_2_obj(self, ms_json):
        self.user_id = ms_json['user_id']
        self.time = ms_json['time']
        self.name = ms_json['name']

    def fill_slot(self, entities, uid):
        #entities格式 {['value':'','entity':''],['value':'','entitiy':''}
        self.user_id = uid
        if len(entities):#实体非空
            for ent in entities:
                if ent['entity'] == "time":
                    self.time = ent['value']

    def handle(self):
        if self.time is None:#处理意图，槽未被填充
            # 把对话场景写到redis缓存中，构造对话场景
            r.set(str(self.user_id), str(self.obj_2_json()))
            r.expire(str(self.user_id), 60)
            return "请问你想查询哪一天的药方，只能查今天或者明天的哦"
        else:
            #完成意图处理，清除对话场景
            return self.search_medicine()

    def search_medicine(self):
        # 根据user_id和时间到mysql数据库查询药单
        if self.time != "今天" and self.time != "明天":
            return "只能查今天或者明天的哦"
        r.delete(str(self.user_id))
        return "您应该吃枣药丸"


class CostSearch:
    user_id = None
    name = 'cost_search'

    def __init__(self):
        user_id = None
        name = 'cost_search'

    def handle(self):
        #根据user_id查询数据库获取费用
        return "您需要支付16元"


class WeatherSearch:
    user_id = None
    name = 'weather_search'
    location = None
    time = None

    def obj_2_json(self):
        return {
            'user_id': self.user_id,
            'location': self.location,
            'name': self.name,
            'time': self.time
        }

    def json_2_obj(self, ws_json):
        self.user_id = ws_json['user_id']
        self.location = ws_json['location']
        self.name = ws_json['name']
        self.time = ws_json['time']

    def __init__(self):
        user_id = None
        name = 'weather_search'
        location = None
        time = None

    def handle(self):
        if self.location is not None and self.time is not None:
            r.delete(str(self.user_id))
            return str(self.location) + self.time + "的天气..."
        else:
            r.set(str(self.user_id), str(self.obj_2_json()))
            r.expire(str(self.user_id), 60)
            if self.time is None and self.location is None:
                return "请问您想查询什么地方什么时间的天气"
            elif self.time is None:
                return "请问您想查询什么时间的天气"
            else:
                return "请问你想查询哪个地方的天气"

    def fill_slot(self, entities, uid):
        #entities格式 {['value':'','entity':''],['value':'','entitiy':''}
        self.user_id = uid
        if len(entities):#实体非空
            for ent in entities:
                if ent['entity'] == "location":
                    self.location = ent['value']
                if ent['entity'] == "time":
                    self.time = ent['value']


class Book:
    user_id = None
    name = 'book'
    doctor = None
    time = None
    hour = None
    phone = None

    def __init__(self):
        self.user_id = None
        self.name = 'book'
        self.doctor = None
        self.time = None
        self.phone = None
        self.hour = None

    def obj_2_json(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'doctor': self.doctor,
            'time': self.time,
            'phone': self.phone,
            'hour': self.hour
        }

    def json_2_obj(self, book_json):
        self.user_id = book_json['user_id']
        self.name = book_json['name']
        self.doctor = book_json['doctor']
        self.time = book_json['time']
        self.phone = book_json['phone']
        self.hour = book_json['hour']

    def handle(self):
        success = False
        return_str = ''
        if self.doctor is not None and self.phone is not None and self.time is not None and self.hour is not None:
            success = True
            return_str = "预约成功"
        if self.doctor is None:
            return_str = "请问您想预约哪位医生"
        if self.time is None:
            return_str = "请问您的预约日期"
        if self.hour is None:
            return_str = "请问您的预约时间是几点"
        if self.phone is None:
            return_str = "请问您的手机号是"
        if success:
            r.delete(str(self.user_id))
            return return_str
        else:
            r.set(str(self.user_id), str(self.obj_2_json()))
            r.expire(str(self.user_id), 60)
            return return_str

    def fill_slot(self, entities, uid):
        #entities格式 {['value':'','entity':''],['value':'','entitiy':''}
        self.user_id = uid
        if len(entities):#实体非空
            for ent in entities:
                if ent['entity'] == "name":
                    self.doctor = ent['value']
                if ent['entity'] == "time":
                    self.time = ent['value']
                if ent['entity'] == "phone":
                    self.phone = ent['value']
                if ent['entity'] == "hour":
                    self.hour = ent['value']


@app.route("/chat", methods=['GET', 'POST'])
def hello():
    return_str = ''
    request_str = request.data.decode()
    args = request.args

    if args is not None:
        user_id = args['user_id']
        content = args['content']
        nlu = interpreter.parse(content)
        return_str = str(get_response(nlu, user_id))
        #result = {}
        #result['text'] = return_str
        #return_result = {}
        #return_result['result'] = result
        entities = nlu['entities']
        intent = nlu['intent_ranking'][0]
        return_result = "entities: " + str(entities) + "<br> intent: " + str(intent) + "<br>" + return_str
    elif request_str != '':
        data = eval(request_str)
        user_id = data['user_id']
        content = data['content']
        nlu = interpreter.parse(content)
        return_str = str(get_response(nlu, user_id))
        result = {}
        result['text'] = return_str
        return_result = {}
        return_result['result']=result
    #return json.dumps(return_result)
    return "<h1>" + str(return_result) + "</h1>"


def get_response(nlu, user_id):
    entities = nlu['entities']
    intent = nlu['intent_ranking'][0]
    return handle_intent_request(entities, intent['name'], user_id, None)


def handle_intent_request(entities, intent, user_id, redis_json):
    if intent == "medicine_search":
        return handle_medicine_search(entities, user_id, redis_json)
    elif intent == "confirm":
        return handle_confirm(entities, user_id)
    elif intent == "cost_search":
        return handle_cost_search(entities, user_id)
    elif intent == "greet":
        return "您好，我是机器人小易，请问有什么可以帮到您的"
    elif intent == "weather_search":
        return handle_weather_search(entities, user_id, redis_json)
    elif intent == "deny":
        return "很高兴为您服务"
    elif intent == "book":
        return handle_book(entities, user_id, redis_json)


def handle_book(entities, user_id, redis_json):
    b = Book()
    if redis_json is not None:
        b.json_2_obj(redis_json)
    b.fill_slot(entities, user_id)
    return b.handle()


def handle_weather_search(entities, user_id, redis_json):
    ws = WeatherSearch()
    if redis_json is not None:
        ws.json_2_obj(redis_json)
    ws.fill_slot(entities, user_id)
    return ws.handle()


def handle_medicine_search(entities, user_id, redis_json):
    ms = MedicineSearch()
    if redis_json is not None:
        ms.json_2_obj(redis_json)
    ms.fill_slot(entities, user_id)
    return ms.handle()


def handle_confirm(entities, user_id):
    dialogue = r.get(str(user_id))
    if dialogue is None:
        '''没有对话场景'''
        disease = ""
        for ent in entities:
            if ent['entity'] == "disease":
                disease += ent['value']
        if disease != "":
            return search_disease(disease)
        return "你想告诉我什么?"
    else:
        '''存在上一次对话场景'''
        dialogue = eval(dialogue.decode())
        return handle_intent_request(entities, dialogue['name'], user_id, dialogue)


def search_disease(disease):
    sql = "select linchuangbiaoxian from disease_detail where lemmaTitle = '" + disease + "'"
    if cursor.execute(sql) == 1:
        results = cursor.fetchall()
        return results[0][0]
    sql = "select lemmaTitle from disease_detail where lemmaTitle like '%" + disease + "%'"
    rows = cursor.execute(sql)
    if rows > 1:
        results = cursor.fetchall()
        return_str = "匹配以下疾病，请问您想查询哪一个： "
        for res in results:
            return_str += res[0] + " "
        return return_str
    elif rows == 0:
        return "这超出了我的认知范围"


def handle_cost_search(entities, user_id):
    cs = CostSearch()
    return cs.handle()


if __name__ == '__main__':
    app.run(debug=True)
