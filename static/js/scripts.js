// Gets stocks
(function () {
    fetch("api/stocks/")
        .then(response => response.json())
        .then(stocks => {
            let stockData = JSON.parse(stocks['stocks'])
            stockTableTemplate(stockData);
            let combinationsData = JSON.parse(stocks['combinations'])
            createChart(restructureData(combinationsData))
        });
})();

function restructureData(data) {
    const combinations = {}
    const colors = ['red', 'blue', 'green', 'maroon', 'skyblue', 'yellow', 'tomato', 'purple', 'grey', 'cyan', 'magenta']
    let colorNum = 0
    data.forEach(item => {
        let { symbol, z_score, date_time } = item
        let color = colors[colorNum]

        if (symbol === 'DJI') {
            color = 'black'
        }

        if (!combinations[symbol]) {
            combinations[symbol] = {
                'label': symbol,
                'data': [],
                'date_time': [],
                'fill': false,
                'borderColor': color
            }
            colorNum++
        }

        combinations[symbol]['data'].push(z_score)
        combinations[symbol]['date_time'].push(date_time)
    });

    return Object.values(combinations);
}

function createChart(data) {
    const xValues = data[0]['date_time']
    new Chart("chart", {
        type: "line",
        data: {
            labels: xValues,
            datasets: data
        },
        options: {
            legend: { display: true },
            title: {
                display: true,
                text: "Best Performing Stock Combinations"
            }
        }
    });
};

// Adds CSS classes to price ups/downs
function check_change(num) {
    let className = null;
    if (num > 0) className = 'positive';
    else if (num < 0) className = 'negative';
    return className;
}

// Returns price change compared to previous close
function price_change(stock) {
    const change = stock['close'] - stock['previous_close']
    const percent_change = change * 100 / stock['close']

    return {
        'change': round_nums(change),
        'percent_change': round_nums(percent_change)
    }
}

// Rounds numbers, default is 2 decimal places
function round_nums(num, decimal_places = 100) {
    return Math.round(num * decimal_places) / decimal_places
}

function makeStockDataClickable() {
    const stocks = document.querySelectorAll('.stock');
    stocks.forEach(stock => {
        stock.addEventListener('click', function (e) {
            $('#stock-info-chart').css('display', 'block');
            $('.stock-info-chart-hint').css('display', 'none');
            let symbol = stock.dataset.symbol;
            let company = stock.dataset.company;
            document.querySelector('.stock-title').innerHTML = `${company} (${symbol})`;
            fetch(`api/stocks/${symbol}`)
                .then(response => response.json())
                .then(stock_info => {
                    stockInfoTemplate(stock_info);

                    if (stock_info.num_of_pages > 1) {
                        $('.pagination').css('display', 'block');
                    }

                    $(function () {
                        $('.pagination').pagination({
                            items: stock_info.total_items,
                            itemsOnPage: 10,
                            cssStyle: 'light-theme',
                            onPageClick: function (pageNumber, event) {
                                fetch(`api/stocks/${symbol}?page=${pageNumber}`)
                                    .then(response => response.json())
                                    .then(stock_info => {
                                        stockInfoTemplate(stock_info);
                                    })
                            },
                        });
                    });
                })
        });
    });
};

function stockInfoTemplate(stock_info) {
    let info_chart = '';
    stock_info.data.forEach(info => {
        let change = price_change(info)
        info_chart += `
            <tr>
                <td>${info['open']}</td>
                <td>${info['close']}</td>
                <td>${info['high']}</td>
                <td>${info['low']}</td>
                <td class="${check_change(change['change'])}">${change['change']}</td>
                <td class="${check_change(change['percent_change'])}">${change['percent_change']}</td>
                <td>${info['previous_close']}</td>
                <td>${info['date_time']}</td>
            </tr>
        `;
    });
    document.querySelector('#stock-info-chart-body').innerHTML = info_chart;
}

// Wires up a socket connection to get stock price updates
(function () {
    const url = `ws://${window.location.host}/ws/socket-server/`;
    const chatSocket = new WebSocket(url);

    chatSocket.onmessage = function (e) {
        let stockUpdatedData = JSON.parse(e.data);
        if (stockUpdatedData['type'] === 'stock_update_data') {
            let combinations = JSON.parse(stockUpdatedData['data']['combinations'])
            createChart(restructureData(combinations))
            stocks = JSON.parse(stockUpdatedData['data']['stocks'])
            stockTableTemplate(stocks)
        }
    }
})();

function stockTableTemplate(data) {
    let template = '';
    data.forEach(stock => {
        let change = price_change(stock)
        template += `
            <tr class="stock" data-symbol="${stock['symbol']}" data-company="${stock['company']}" title="Click to see ${stock['symbol']} data.">
                <td>${stock['symbol']}</td>
                <td>${stock['company']}</td>
                <td>${stock['close']}</td>
                <td class="change ${check_change(change['change'])}">${change['change']}</td>
                <td class="change ${check_change(change['percent_change'])}">${change['percent_change']}</td>
                <td>${stock['low']}</td>
                <td>${stock['high']}</td>
                <td>${stock['previous_close']}</td>
                <td>${stock['date_time']}</td>
            </tr>
        `;
    });
    document.getElementById('stock-chart-body').innerHTML = template;
    makeStockDataClickable();
}