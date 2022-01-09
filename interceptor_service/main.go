package main

import (
	"bytes"
	"os"

	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"

	log "github.com/sirupsen/logrus"
	easy "github.com/t-tomalak/logrus-easy-formatter"

	"github.com/go-chi/chi/v5"
)

const ODOO_URL = "http://host.docker.internal:8071/order"
const webhook_token = "Bearer XYZ"

type OrderLine struct {
	ProductId     int     `json:"product_id"`
	ProductUom    int     `json:"product_uom"`
	ProductUomQty int     `json:"product_uom_qty"`
	PriceUnit     float64 `json:"price_unit"`
}

type Order struct {
	Name      string      `json:"name"`
	PartnerId int         `json:"partner_id"`
	CompanyId int         `json:"company_id"`
	DateOrder string      `json:"date_order"`
	OrderItem []OrderLine `json:"order_line"`
}

type Webhook struct {
	Event   string                 `json:"event"`
	Payload map[string]interface{} `json:"payload"`
}

func Register(router chi.Router) {
	router.Get("/", rootHandler)
	router.Post("/order", createOrder)
	router.Get("/order/{id}", getOrder)
	router.Put("/order/{id}", updateOrder)
	router.Post("/webhook", webhookOrder)
}

func requestHandler(w http.ResponseWriter, r *http.Request, url string, method string) {
	var client = &http.Client{}
	var payload Order

	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		log.Error(err)
		return
	}

	jsonData, _ := json.Marshal(payload)
	request, err := http.NewRequest(method, url, bytes.NewBuffer(jsonData))
	if err != nil {
		log.Error(err)
		return
	}

	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("Authorization", r.Header.Get("Authorization"))

	log.Info("sending request to ", url)
	response, err := client.Do(request)
	if err != nil {
		log.Error(err)
		return
	}
	defer response.Body.Close()

	if response == nil {
		return
	}

	result, _ := ioutil.ReadAll(response.Body)
	log.Info("response request from ", ODOO_URL)

	responseHandler(w, response.StatusCode, string(result))
}

func responseHandler(w http.ResponseWriter, code int, payload string) {
	resp := []byte(payload)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	w.Write(resp)
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	var payload = "Service is running"
	responseHandler(w, http.StatusOK, payload)
}

func createOrder(w http.ResponseWriter, r *http.Request) {
	requestHandler(w, r, ODOO_URL, http.MethodPost)
}

func getOrder(w http.ResponseWriter, r *http.Request) {
	url := fmt.Sprintf(ODOO_URL+"/%s", chi.URLParam(r, "id"))
	requestHandler(w, r, url, http.MethodGet)
}

func updateOrder(w http.ResponseWriter, r *http.Request) {
	url := fmt.Sprintf(ODOO_URL+"/%s", chi.URLParam(r, "id"))
	requestHandler(w, r, url, http.MethodPut)
}

func webhookOrder(w http.ResponseWriter, r *http.Request) {
	var payload Webhook

	auth := r.Header.Get("Authorization")

	if auth != webhook_token {
		log.Error("Webhook Token Unauthorized")
		return
	}

	if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
		log.Error(err)
		return
	}

	out, err := json.Marshal(payload)
	if err != nil {
		log.Error(err)
		return
	}

	log.Info(string(out))
}

func init() {
	log2 := &log.Logger{
		Out:   os.Stderr,
		Level: log.DebugLevel,
		Formatter: &easy.Formatter{
			TimestampFormat: "2006-01-02 15:04:05",
			LogFormat:       "[%lvl%]: %time% - %msg%\n",
		},
	}

	log.SetFormatter(log2.Formatter)
}

func main() {
	// server & endpoint

	r := chi.NewRouter()
	r.Group(func(c chi.Router) {
		Register(c)
	})

	log.Info("server started at localhost:8000")

	http.ListenAndServe(fmt.Sprintf(":8000"), r)

}
