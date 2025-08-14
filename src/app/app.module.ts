import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { ArticleInputComponent } from './components/article-input/article-input.component';
import { ArticleOutputComponent } from './components/article-output/article-output.component';
import { LanguageSelectorComponent } from './components/language-selector/language-selector.component';
import { FooterComponent } from './components/footer/footer.component';
import { HomeComponent } from './pages/home/home.component';

import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { CompareModelOutputComponent } from './components/compare-model-output/compare-model-output.component';
import { SimplifyProcessComponent } from './components/simplify-process/simplify-process.component';
import { MetricsOutputComponent } from './components/metrics-output/metrics-output.component';


@NgModule({
  declarations: [
    AppComponent,
    ArticleInputComponent,
    ArticleOutputComponent,
    LanguageSelectorComponent,
    FooterComponent,
    HomeComponent,
    CompareModelOutputComponent,
    SimplifyProcessComponent,
    MetricsOutputComponent
  ],
  imports: [
    FormsModule,
    BrowserModule,
    AppRoutingModule,
    HttpClientModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
