package com.example.sampleapp.ui.dashboard;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import com.hunter.library.debug.HunterDebug;
import android.content.Context;

public class DashboardViewModel extends ViewModel {

    private MutableLiveData<String> mText;

    @HunterDebug
    public DashboardViewModel() {
        mText = new MutableLiveData<>();
        mText.setValue("This is dashboard fragment");
    }

    @HunterDebug
    public LiveData<String> getText() {
        return mText;
    }
}
