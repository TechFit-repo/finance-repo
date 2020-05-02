## app.R ##
library(shinydashboard)
library(png)
library(shinydashboardPlus)
library(shiny)
library(rdrop2)
library(dplyr)
library(tidyverse)
library(magrittr)
library(highcharter)
library(shinyjs)

setwd("//Users//greengodfitness//Desktop///TechFit//finance-repo//techfit-finance-repo//app")
title <- tags$a(href='https://www.google.com',
                icon("diamond"), 'TechFit')

master_account <- drop_read_csv("Transactions/Master_Account.csv")
monthly_tax <- drop_read_csv("Transactions/Monthly_Tax.csv")

ui <- dashboardPagePlus(skin='black',
  dashboardHeaderPlus(title = title),
  dashboardSidebar(width=275,
                   
                   # Logout Output 
                   
                   # Custom CSS to hide the default logout panel
                   tags$head(tags$style(HTML('.shiny-server-account {display:session$user}'))),
                   
                   # The dynamically-generated user panel
                   uiOutput("userpanel"),
                   
                   ############### Side Bar Menu ################
                   
                   sidebarMenu(style = "position: Scroll; overflow: visible;",id = "sidebarmenu",
                   
                   menuItem("Account Overview", tabName = "iaa", icon = icon("th")))
                  ),
  dashboardBody(
    # Boxes need to be put in a row (or column)
     fluidRow(column(10, offset = 0.5, h1("ACCOUNT OVERVIEW"))),
     br(),
     br(),
     box(
       solidHeader = FALSE,
       title = "Account Summary",
       background = NULL,
       width = 12,
       status = "danger",
       footer = fluidRow(
         column(
           width = 6,
           descriptionBlock(
             number = mean(monthly_tax$Net_Income),
             number_color = "green",
             number_icon = "fa fa-caret-up",
             header = sum(monthly_tax$Net_Income),
             text = "INCOME",
             right_border = FALSE,
             margin_bottom = FALSE
           )
         ),
         column(
           width = 6,
           descriptionBlock(
             number = mean(monthly_tax$Debit),
             number_color = "red",
             number_icon = "fa fa-caret-down",
             text = "EXPENSES",
             right_border = FALSE,
             margin_bottom = FALSE
           )
         )
       )
     ),
     
     box(
       title = "Overall Profile",
       status = "primary",
       width = 12,
       boxProfile(
         src = "bank-flat.png",
         title = "Tech Fit",
         subtitle = "Tech & Fitness",
         boxProfileItemList(
           bordered = TRUE,
           boxProfileItem(
             title = "Gross Income",
             description = sum(monthly_tax$Credit)
           ),
           boxProfileItem(
             title = "Tax",
             description = sum(monthly_tax$Overall_Tax)
           ),
           boxProfileItem(
             title = "Net Income",
             description = sum(monthly_tax$Net_Income)
         )
       )
     )
    ),
     
    highchartOutput("highchartcustomer_1"),
    br(),
    br(),
    highchartOutput("highchartcustomer_2"),
    br(),
    br(),
    highchartOutput("highchartcustomer_3"),
    br(),
    br(),
    fluidRow(
      DT::dataTableOutput('table')
    )
)
)
server <- function(input, output) {
  
  addClass(selector = "body", class = "sidebar-collapse")
  
  output$highchartcustomer_1 <- renderHighchart({
    hc <- master_account %>% group_by(Category) %>% summarise(Expenses = sum(Debit)) %>% drop_na(Expenses)
    highchart() %>%
      hc_xAxis(categories = hc$Category, title= list(text="Category")) %>%
      hc_yAxis(title=list(text="Amount")) %>%
      hc_add_series(data = hc$Expenses,
                    name = "Expense Category",
                    color = c("#004687")) %>%
      hc_tooltip(table = TRUE, sort= TRUE, crosshairs=FALSE,backgroundColor = "white",
                  shared=TRUE, borderWidth = 1)%>%
      hc_title(text = "<b> Expenses Based on Category</b>",
               margin=40,align="center",
               style = list(color= "#004687", useHTML =TRUE, fontfamily = "Calibri")) %>%
      hc_chart(type = "column",
               options3d = list(enabled = FALSE, beta = 15, alpha = 15)) %>%
      hc_exporting(enabled=TRUE) %>%
      hc_plotOptions(
        series = list(
          boderWidth = 0,
          marker = list(enabled = FALSE)
        )
      )
      })
  
  output$highchartcustomer_2 <- renderHighchart({
    hc <- master_account %>% group_by(Date) %>% summarise(Expenses = sum(Debit)) %>% drop_na(Expenses)
    highchart() %>%
      hc_xAxis(categories = hc$Date, title=list(text="Date")) %>%
      hc_yAxis(title=list(text="Amount")) %>%
      hc_add_series(data = hc$Expenses,
                    name = "Expenses",
                    color = c("#004687")) %>%
      hc_tooltip(table = TRUE, sort = TRUE,crosshairs = FALSE, backgroundColor = "white",
                 shared = TRUE, borderWidth = 1) %>%
      hc_title(text = "<b>Expenses Based on Date</b>",
               margin = 40, align = "center",
               style = list(color = "#004687", useHTML = TRUE, fontfamily = "Calibri")) %>%
      hc_chart(type = "line",
               options3d = list(enabled = FALSE, beta = 15, alpha = 15)) %>%
      hc_exporting(enabled = TRUE)%>%
      hc_plotOptions(
        series = list(
          boderWidth = 0,
          marker = list(enabled = FALSE)))
  }) # render Highchart 2
  
  output$highchartcustomer_3 <- renderHighchart({
    hc <- master_account %>% drop_na(Credit) %>% filter(isTaxableIncome == 'Y' & Description != 'TRANSFER') %>% group_by(Date) %>% summarise(Income = sum(Credit))
    highchart() %>%
      hc_xAxis(categories = hc$Date, title=list(text="Date")) %>%
      hc_yAxis(title=list(text="Amount")) %>%
      hc_add_series(data = hc$Income,
                    name = "Income",
                    color = c("#004687")) %>%
      hc_tooltip(table = TRUE, sort = TRUE,crosshairs = FALSE, backgroundColor = "white",
                 shared = TRUE, borderWidth = 1) %>%
      hc_title(text = "<b>Income Based on Date</b>",
               margin = 40, align = "center",
               style = list(color = "#004687", useHTML = TRUE, fontfamily = "Calibri")) %>%
      hc_chart(type = "line",
               options3d = list(enabled = FALSE, beta = 15, alpha = 15)) %>%
      hc_exporting(enabled = TRUE)%>%
      hc_plotOptions(
        series = list(
          boderWidth = 0,
          marker = list(enabled = FALSE)))
  }) # render Highchart 3
  
  output$table <- DT::renderDataTable(master_account, filter = 'top', options = list(
    pagelength = 5, autoWidth = TRUE), class = 'cell-border stripe'
  )
  
}

shinyApp(ui, server)