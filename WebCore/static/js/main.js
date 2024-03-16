
class Utils {
    post(data, callback) {
        let xhr = new XMLHttpRequest();
        xhr.open("POST", "", true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function (res) { callback(JSON.parse(res.currentTarget.response)) };
        data["Authorization"] = tg.initData;
        xhr.send(JSON.stringify(data));
    }
}

class RufflePrizesBetsPage {
    open_page() {
        document.querySelector("#all-draws-page").style.display = "none";
        document.querySelector("#detailed-draw-page").style.display = "none";
        document.querySelector("#ruffle-prizes-bets-page").style.display = "block";

        tg.BackButton.show()
        tg.BackButton.onClick(all_draws.open_page)
    }

    getAndAddBets() {
        utils.post({"method": "get_user_bets"}, (response)=>{
            if (response["bets"] === null) {return}
            response["bets"].reverse().forEach((i)=>{
                this.add_bet(i["ruffle_prizes_title"], i["bet_amount"],i["bet_time"])
            })
        });
    }

    add_bet(draw_name, amount, time) {
        const date = new Date(time);
        const day = date.getDate().toString().padStart(2, "0");
        const month = (date.getMonth() + 1).toString().padStart(2, "0");
        const year = date.getFullYear();
        const hour = date.getHours().toString().padStart(2, "0");
        const minute = date.getMinutes().toString().padStart(2, "0");
        const formattedDate = `${day}-${month}-${year} ${hour}:${minute}`;

        let el = document.querySelector("#ruffle-prizes-bets-page");
        el.innerHTML = `
            <div class="collapsible_background">
                <button class="collapsible" onclick="collapsible_event(this)">${draw_name}</button>
                <div class="content">
                    <p>Розыгрыш: ${draw_name}<br>Ставка: ${amount}<br>Время: ${formattedDate}</p>
                </div>
            </div>   
        ` + el.innerHTML
    }
}

class DetailedDrawPage {
    constructor() {
        this.opened_page_draw_id = null
    }
     open_page(draw_id) {
        let draw = all_draws.get_all_draws()[draw_id]

        // Заполнение фотографий
        let photos = (draw["photos"] === null) ? JSON.parse(draw["low_quality_photos"]) : JSON.parse(draw["photos"])
        let img_style = (draw["photos"] === null) ? "filter: blur(20px); box_shadow: 0 0 10px 5px transparent;" : "filter: none; box_shadow: none;"
        let photos_html =  ``;
        if (photos !== null) {
            photos.forEach(photo => {
                photos_html += `
                    <swiper-slide class="slide"><img src="data:image/png;base64, ${photo}" style="${img_style}" alt=""/></swiper-slide>
                `});
        } else {
            photos_html += `<swiper-slide class="slide"><div style="height: 300px; ${img_style}"></div></swiper-slide>`
        }

        // Ставить кнопку 'Сделать ставку', или список победивших
        let end_html;
        if ("users_bets" in draw) {
            let users_bets_html = ``
            let users_bets = JSON.parse(draw["users_bets"])
            for (let i in users_bets) { users_bets_html += `<p>${i} - ${users_bets[i]}</p` }
            end_html = `
                <p class="detailed-draw-parameters">Победитель: ${draw['winner_id']}</p>
                <div class="collapsible_background">
                    <button class="collapsible" onclick="collapsible_event(this)">Ставки всех пользователей</button>
                    <div class="content">
                        ${users_bets_html}
                    </div>
                </div> 
            `
        } else {
            end_html = `<button id="participate-button" onclick="detailed_draws.draw_prizes_bet_popup(${draw['id']})">Сделать ставку</button>`
        }

        // Узнаем оставшееся время до подведения розыгрыша
         if (draw["countdown_start_time"] !== null && !(draw["is_over"])) {
             let start_time = new Date(draw["countdown_start_time"]);
             let current_time = new Date();
             let timeDiff = current_time.getTime() - start_time.getTime();
             console.log(start_time)
             console.log(current_time)
             var time_left = `Осталось времени: ${draw["countdown_hours"] - Math.floor(timeDiff / (1000 * 60 * 60))}ч`;
         } else if (draw["is_over"]) {
             var time_left = "Отсчет времени завершился!"
         } else {
             var time_left = "Отсчет  времени еще не начался!"
         }

        document.querySelector("#detailed-draw-page").innerHTML = `
            <swiper-container pagination="true" id="detailed-draw-photos">${photos_html}</swiper-container>      
            <div style="width: 95%; height: auto; margin: 10px auto 0 auto">
                <p id="detailed-draw-title" class="detailed-draw-parameters" style="font-size: 20px">${draw['title']}</p>
                <p class="detailed-draw-parameters" id="detailed-draw-money-collected">Собрано: ${draw['money_collected']}/${draw['money_needed']}</p>
                <p class="detailed-draw-parameters">${time_left}</p>
                <div class="collapsible_background">
                    <button class="collapsible" onclick="collapsible_event(this)">Описание товара</button>
                    <div class="content">
                        <p>${draw['description']}</p>
                    </div>
                </div>   
                ${end_html}  
            </div>    
        `

        document.querySelector("#all-draws-page").style.display = "none";
        document.querySelector("#detailed-draw-page").style.display = "block";
        document.querySelector("#ruffle-prizes-bets-page").style.display = "none";

        tg.BackButton.show()
        tg.BackButton.onClick(all_draws.open_page)
        this.opened_page_draw_id = draw_id
    }

    draw_prizes_bet_popup(draw_id) {
         Swal.fire({
            html: `
                <h1>Ставка</h1>
                <p class="detailed-draw-parameters" style="margin-bottom: 10px; font-size: 17px;height: 40px">Ваш баланс: ${user_information["balance"]}₴</p>
                <input id="input_draw_prizes_bet" placeholder="Введите ставку" type="number">
                <button id="send_draw_prizes_bet" onclick="detailed_draws.try_create_bet(${draw_id})">Создать</button>`,
            showConfirmButton: false,
            showCancelButton: false,
            heightAuto: false,
            customClass: {
                htmlContainer: "popup-add-dialog-container-html",
                popup: "popup-add-dialog-popup"
            }
        });
    }

    try_create_bet(draw_id) {
        let bet = document.querySelector("#input_draw_prizes_bet")
        if (bet.value !== "") {
            utils.post(
                {method: "create_draw_prizes_bet", draw_id: draw_id, bet: bet.value},
                (response)=>{
                    if (response["ok"] === true) {
                        user_information["balance"] = response["new_balance"]
                        bets.add_bet(response["bet"]["ruffle_prizes_title"], response["bet"]["bet_amount"], response["bet"]["bet_time"])

                        let ruffle_id = response["bet"]["ruffle_prizes_id"]
                        let list_of_draws = all_draws.get_all_draws()
                        if (ruffle_id in list_of_draws) {
                            list_of_draws[ruffle_id]["money_collected"] += response["bet"]["bet_amount"]
                            let money_collected = list_of_draws[ruffle_id]["money_collected"]
                            let money_needed = list_of_draws[ruffle_id]["money_needed"]
                            document.querySelector("#detailed-draw-money-collected")
                                .innerHTML = `Собрано: ${money_collected}/${money_needed}`
                            document.querySelector(`#ruffle-prizes-${ruffle_id} button`)
                                .innerHTML = `${money_collected}/${money_needed}`
                        }

                        if (!(ruffle_id in all_draws.draws.get("participate"))) {
                            all_draws.draws.get("participate")[ruffle_id] = list_of_draws[ruffle_id]
                            all_draws.reset_draws_statistic("*")
                        }

                        Swal.fire({
                            title: "Запрос принят!",
                            text: "Ставка сделана! Удачи в розыгрыше :)",
                            showConfirmButton: false,
                            showCancelButton: false,
                        });
                    } else {
                        Swal.fire({
                            title: "Ошибка!",
                            text: response["error"],
                            showConfirmButton: false,
                            showCancelButton: false,
                        });
                    }
                }
            );
        }
        bet.value = ""
    }
}



class AllDrawsPage {
    constructor() {
        this.draws = new Map();

        // Переключение фильтров для показа списка розыгрышей
        ///////////////////////////////////////////////////////////////
        let set_color_for_statistic_boxes = (active, participate, closed) => {
            document.querySelector("#statistic_active").style.background = `#FFFFFF${active}`
            document.querySelector("#statistic_participate").style.background = `#FFFFFF${participate}`
            document.querySelector("#statistic_closed").style.background = `#FFFFFF${closed}`
        }
        set_color_for_statistic_boxes(80, 20, 20)
        document.querySelector("#statistic_active").addEventListener("click", ()=>{
            set_color_for_statistic_boxes(80, 20, 20)
            this.show_filtered_draws("active")
        });
        document.querySelector("#statistic_participate").addEventListener("click", ()=>{
            set_color_for_statistic_boxes(20, 80, 20)
            this.show_filtered_draws("participate")
        });
        document.querySelector("#statistic_closed").addEventListener("click", ()=>{
            set_color_for_statistic_boxes(20, 20, 80)
            this.show_filtered_draws("closed")
        });
    }

    load_high_quality_photos() {
        utils.post(
            {method: "load_high_quality_photos"},
            (response) => {
                response["prize_draws"].forEach(draw => {
                    if (draw["id"] in this.draws.get("active")) {this.draws.get("active")[draw["id"]]["photos"] = draw["photos"]}
                    if (draw["id"] in this.draws.get("participate")) { this.draws.get("participate")[draw["id"]]["photos"] = draw["photos"]}
                    if (draw["id"] in this.draws.get("closed")) { this.draws.get("closed")[draw["id"]]["photos"] = draw["photos"]}

                    // Обновляем страницу с детальным описанием, если она открыта
                    if (detailed_draws.opened_page_draw_id === draw["id"]) {detailed_draws.open_page(draw["id"])}
                })
            }
        )
    }

    open_page() {
        tg.BackButton.hide()
        document.querySelector("#all-draws-page").style.display = "block";
        document.querySelector("#detailed-draw-page").style.display = "none";
        document.querySelector("#ruffle-prizes-bets-page").style.display = "none";
    }

    show_filtered_draws(filter_name) {
        let parentElement = document.querySelector("#list-draws-of-prizes")
        while (parentElement.firstChild) {
          parentElement.removeChild(parentElement.firstChild);
        }
        for (let key in this.draws.get(filter_name)) {
            this.add_draw(this.draws.get(filter_name)[key])
        }
    }

    get_all_draws() {
        return Object.assign({}, this.draws.get("active"), this.draws.get("participate"), this.draws.get("closed"));
    }

    reset_draws_statistic(filter_name="*") {
        if (filter_name==="active" || filter_name==="*") {
            document.querySelector("#statistic_active").innerHTML = Object.keys(this.draws.get("active")).length;
        }
        if (filter_name==="participate" || filter_name==="*") {
            document.querySelector("#statistic_participate").innerHTML = Object.keys(this.draws.get("participate")).length;
        }
        if (filter_name==="closed" || filter_name==="*") {
            document.querySelector("#statistic_closed").innerHTML = Object.keys(this.draws.get("closed")).length;
        }
    }

    reset_prize_draws_list() {
        this.clear_all_draws()
        this.draws.set("active", {})
        this.draws.set("participate", {})
        this.draws.set("closed", {})

        let set = (filter, prize_draws) => {
            prize_draws.forEach((value, _) => {
                this.draws.get(filter)[value["id"]] = value
            })
        }
        utils.post({method: "get_prize_draws", type: "active"}, (response)=>{
            set("active", response["prize_draws"])
            this.reset_draws_statistic("active")
            this.show_filtered_draws("active")
        });
        utils.post({method: "get_prize_draws", type: "participate"}, (response)=>{
            set("participate", response["prize_draws"])
            this.reset_draws_statistic("participate")
        });
        utils.post({method: "get_prize_draws", type: "closed"}, (response)=>{
            set("closed", response["prize_draws"])
            this.reset_draws_statistic("closed")
        });

        this.load_high_quality_photos();
    }
    
    add_draw(draw) {
        document.querySelector("#list-draws-of-prizes").innerHTML += `
            <li onclick="detailed_draws.open_page(${draw["id"]})" id="ruffle-prizes-${draw["id"]}">
                <div class="all-draws-of-prizes-background" id="draw_prizes_${draw["id"]}">
                    <img src="data:image/png;base64, ${draw["menu_icon"]}" alt=""/>
                    <p class="title">${draw["title"]}</p>
                </div>
                <button class="collected">${draw["money_collected"]}/${draw["money_needed"]}</button>
            </li>
        `;
    }

    clear_all_draws() {
        this.draws.clear()
        document.querySelector("#list-draws-of-prizes").innerHTML = "";
    }
}


const tg = Telegram.WebApp;
const utils = new Utils();
const all_draws = new AllDrawsPage();
const detailed_draws = new DetailedDrawPage();
const bets = new RufflePrizesBetsPage();

// Устанавливаем цвета из Telegram
////////////////////////////////////////////
tg.themeParams.bg_color = "#222139"
tg.themeParams.secondary_bg_color = "#37355E"
tg.themeParams.text_color = "#FFFFFF"

// Расширяем цветовую палитру
//////////////////////////////////////////////
for (const [key, value] of Object.entries(tg.themeParams)) {
    const cssKey = `--${key.replaceAll("_", "-")}`;
    document.documentElement.style.setProperty(cssKey, value);

    for (let i = 10; i < 100; i += 10) {
        document.documentElement.style.setProperty(`${cssKey}-${i}`, `${value}${i}`);
    }
}

// Делаем WEBAPP на весь экран
////////////////////////////////////
tg.expand();

// Загружаем информацию о пользователе
////////////////////////////////////
let user_information;
utils.post({"method": "get_user_data"}, (user_data)=>{
    user_information = user_data
    let firstname_el = document.querySelector("#firstname");
    let user_photo_el = document.querySelector("#user_avatar");
    if("photo" in user_data) {user_photo_el.src = "data:image/png;base64, " + user_data["photo"]}
    if("firstname" in user_data) {firstname_el.innerHTML = user_data["firstname"]}
    else {firstname_el.innerHTML = "Anonymous"}
});

// Подгружаем розыгрыши
all_draws.reset_prize_draws_list()
bets.getAndAddBets()
